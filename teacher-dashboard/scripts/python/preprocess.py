"""
OULAD Preprocessing Script — Vectorised & Parallel
===================================================
All CSVs are loaded into DataFrames upfront. Aggregation uses pandas groupby
and numpy matrix operations. Each course is processed by a worker from a
ProcessPoolExecutor so all courses run concurrently.

Usage:
    python scripts/python/preprocess.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

ROOT     = Path(__file__).resolve().parents[2]
CSV_DIR  = ROOT / "public" / "data" / "oulad"
OUT_DIR  = ROOT / "public" / "processed"
LSTM_TRAJ_CSV  = OUT_DIR / "lstm_trajectory_table.csv"
LSTM_HORIZONS  = ["w05", "w10", "w15", "w20", "w25"]   # column suffix order
HORIZON_CUTOFF = [5, 10, 15, 20, 25]                    # week at which each model activates

DECAY_LAMBDA = 0.15


# ── Helpers ───────────────────────────────────────────────────────────────────

def csv_path(name: str) -> Path:
    p = CSV_DIR / name
    if not p.exists():
        sys.exit(f"\n❌ Missing: {p}\nPlace all 7 OULAD CSV files in: {CSV_DIR}\n")
    return p


def build_decay_matrix(n: int) -> np.ndarray:
    """Lower-triangular (n×n) weight matrix: W[t,τ] = exp(-λ(t-τ)) for τ≤t."""
    t = np.arange(n, dtype=np.float32)
    return np.tril(np.exp(-DECAY_LAMBDA * (t[:, None] - t[None, :])))


# ── Per-course worker (runs in subprocess) ───────────────────────────────────

def process_course(bundle: dict) -> tuple[str, dict | None]:
    mod = bundle["mod"]
    pres = bundle["pres"]
    T = bundle["num_weeks"]
    key = f"{mod}_{pres}"

    students_df    = pd.DataFrame(bundle["students"])
    regs_df        = pd.DataFrame(bundle["regs"])
    assess_meta_df = pd.DataFrame(bundle["assess_meta"])
    vle_df         = pd.DataFrame(bundle["vle"])     # id_student, week, clicks
    scores_df      = pd.DataFrame(bundle["scores"])  # id_student, id_assessment, score, date_submitted

    if students_df.empty:
        return key, None

    student_ids = students_df["id_student"].to_numpy(dtype=np.int64)
    S = len(student_ids)
    sid_idx: dict[int, int] = {int(s): i for i, s in enumerate(student_ids)}

    # ── Weekly clicks matrix (S × T) via numpy scatter-add ───────────────────
    clicks_mat = np.zeros((S, T), dtype=np.float32)
    if not vle_df.empty:
        v = vle_df.copy()
        v["sidx"] = v["id_student"].map(sid_idx)
        v = v.dropna(subset=["sidx"])
        v["sidx"] = v["sidx"].astype(np.int32)
        v = v[(v["week"] >= 0) & (v["week"] < T)]
        np.add.at(
            clicks_mat,
            (v["sidx"].to_numpy(), v["week"].to_numpy(dtype=np.int32)),
            v["clicks"].to_numpy(dtype=np.float32),
        )

    # ── Decayed engagement (S × T) = clicks_mat @ W.T ────────────────────────
    decayed_mat = clicks_mat @ build_decay_matrix(T).T   # (S × T)

    # ── Cohort P75 per week ───────────────────────────────────────────────────
    p75 = np.maximum(np.percentile(decayed_mat, 75, axis=0), 5.0)   # (T,)

    # ── Registration active mask (S × T) ─────────────────────────────────────
    reg_day   = np.zeros(S, dtype=np.float32)
    unreg_day = np.full(S, np.inf, dtype=np.float32)

    if not regs_df.empty:
        regs_idx = regs_df.set_index("id_student")
        for i, sid in enumerate(student_ids):
            if sid in regs_idx.index:
                row = regs_idx.loc[sid]
                rd, ud = row["date_registration"], row["date_unregistration"]
                if not pd.isna(rd):
                    reg_day[i] = float(rd)
                if not pd.isna(ud):
                    unreg_day[i] = float(ud)

    current_days = (np.arange(T, dtype=np.float32) + 1) * 7   # (T,)
    active = (                                                   # (S × T) bool
        (reg_day[:, None]   <= current_days[None, :]) &
        (unreg_day[:, None] >= current_days[None, :])
    )

    # ── Assessment matrices (S × A) ───────────────────────────────────────────
    A = len(assess_meta_df)
    has_assess = A > 0

    if has_assess:
        aid_arr      = assess_meta_df["id_assessment"].to_numpy(dtype=np.int64)
        date_nan     = assess_meta_df["date"].isna().to_numpy()
        weight_nan   = assess_meta_df["weight"].isna().to_numpy()
        date_due     = np.where(date_nan,   np.inf, assess_meta_df["date"].to_numpy(dtype=np.float32))
        weight_vec   = np.where(weight_nan, 0.0,    assess_meta_df["weight"].to_numpy(dtype=np.float32))
        assess_types = assess_meta_df["assessment_type"].tolist()
        aid_idx: dict[int, int] = {int(a): j for j, a in enumerate(aid_arr)}

        score_mat   = np.full((S, A), np.nan, dtype=np.float32)
        sub_day_mat = np.full((S, A), np.nan, dtype=np.float32)

        if not scores_df.empty:
            sc = scores_df.copy()
            sc["sidx"] = sc["id_student"].map(sid_idx)
            sc["aidx"] = sc["id_assessment"].map(aid_idx)
            sc = sc.dropna(subset=["sidx", "aidx"])
            sc["sidx"] = sc["sidx"].astype(np.int32)
            sc["aidx"] = sc["aidx"].astype(np.int32)

            has_sc = ~sc["score"].isna()
            score_mat[
                sc.loc[has_sc, "sidx"].to_numpy(),
                sc.loc[has_sc, "aidx"].to_numpy(),
            ] = sc.loc[has_sc, "score"].to_numpy(dtype=np.float32)

            has_ds = ~sc["date_submitted"].isna()
            sub_day_mat[
                sc.loc[has_ds, "sidx"].to_numpy(),
                sc.loc[has_ds, "aidx"].to_numpy(),
            ] = sc.loc[has_ds, "date_submitted"].to_numpy(dtype=np.float32)

    # ── LSTM trajectory matrices (one per horizon) ───────────────────────────
    # traj_mats[h] = S × T array for horizon LSTM_HORIZONS[h]
    traj_mats: list[np.ndarray] = [np.full((S, T), np.nan, dtype=np.float32) for _ in LSTM_HORIZONS]

    if bundle.get("lstm_risks"):
        lr = pd.DataFrame(bundle["lstm_risks"])
        lr["sidx"] = lr["id_student"].map(sid_idx)
        lr = lr.dropna(subset=["sidx"])
        lr["sidx"] = lr["sidx"].astype(np.int32)
        lr = lr[(lr["week"] >= 0) & (lr["week"] < T)]
        rows = lr["sidx"].to_numpy()
        cols = lr["week"].to_numpy(dtype=np.int32)
        for h, hz in enumerate(LSTM_HORIZONS):
            col = f"risk_{hz}"
            if col in lr.columns:
                traj_mats[h][rows, cols] = lr[col].to_numpy(dtype=np.float32)

    # lstm_mat: at each week use the freshest horizon whose cutoff <= week+1,
    # else fall back to the earliest horizon (w05).
    lstm_mat = np.full((S, T), np.nan, dtype=np.float32)
    for w in range(T):
        current_week_1 = w + 1   # 1-indexed week number
        # pick the highest horizon whose cutoff does not exceed current week
        h_idx = 0
        for h, cutoff in enumerate(HORIZON_CUTOFF):
            if current_week_1 >= cutoff:
                h_idx = h
        lstm_mat[:, w] = traj_mats[h_idx][:, w]

    # ── Vectorised risk & tier (S × T) ───────────────────────────────────────
    # LSTM predictions take priority; heuristic fills any remaining gaps.
    risk_mat = np.full((S, T), np.nan, dtype=np.float32)
    tier_mat = np.full((S, T), np.nan, dtype=np.float32)

    for w in range(T):
        active_w = active[:, w]
        if not active_w.any():
            continue

        engagement = np.minimum(1.0, decayed_mat[:, w] / float(p75[w]))  # (S,)

        if has_assess:
            due_j = date_due <= current_days[w]   # (A,) bool
            n_due = int(due_j.sum())
        else:
            n_due = 0

        if n_due > 0:
            dw       = weight_vec * due_j          # (A,) — zero for non-due
            total_dw = float(dw.sum())

            ontime     = (~np.isnan(sub_day_mat)) & (sub_day_mat <= current_days[w])
            due_ontime = ontime & due_j[None, :]   # (S × A)

            a_perf   = (np.where(due_ontime, score_mat / 100.0, 0.0) * dw[None, :]).sum(axis=1) / max(total_dw, 1e-9)
            sub_rate = due_ontime.sum(axis=1) / n_due
        else:
            a_perf   = np.zeros(S, dtype=np.float32)
            sub_rate = np.zeros(S, dtype=np.float32)

        heuristic_w = np.clip(
            1.0 - (0.45 * a_perf + 0.35 * engagement + 0.20 * sub_rate), 0.0, 1.0
        )

        has_lstm = ~np.isnan(lstm_mat[:, w])
        risk_w   = np.round(np.where(has_lstm, lstm_mat[:, w], heuristic_w), 4)
        tier_w   = np.where(risk_w < 0.33, 1, np.where(risk_w < 0.66, 2, 3))

        risk_mat[active_w, w] = risk_w[active_w]
        tier_mat[active_w, w] = tier_w[active_w]

    # ── Serialise student records ─────────────────────────────────────────────
    reg_day_out   = reg_day.astype(np.int32)
    unreg_day_out = np.where(np.isinf(unreg_day), -1, unreg_day.astype(np.int32))

    processed_students = []
    for i, srow in enumerate(students_df.itertuples(index=False)):
        student_assessments = []
        if has_assess:
            for j in range(A):
                student_assessments.append({
                    "id_assessment":   int(aid_arr[j]),
                    "assessment_type": assess_types[j],
                    "date_due":        None if date_nan[j]   else int(date_due[j]),
                    "weight":          None if weight_nan[j] else float(weight_vec[j]),
                    "score":           None if np.isnan(score_mat[i, j])   else round(float(score_mat[i, j]),   2),
                    "date_submitted":  None if np.isnan(sub_day_mat[i, j]) else int(sub_day_mat[i, j]),
                })

        ud = int(unreg_day_out[i])
        def _traj(arr: np.ndarray) -> list:
            return [None if math.isnan(float(v)) else round(float(v), 4) for v in arr]

        processed_students.append({
            "id_student":           int(srow.id_student),
            "gender":               str(srow.gender),
            "region":               str(srow.region),
            "highest_education":    str(srow.highest_education),
            "imd_band":             None if pd.isna(srow.imd_band) else str(srow.imd_band),
            "age_band":             str(srow.age_band),
            "num_of_prev_attempts": int(srow.num_of_prev_attempts),
            "studied_credits":      int(srow.studied_credits),
            "disability":           str(srow.disability) == "Y",
            "final_result":         str(srow.final_result),
            "date_registration":    int(reg_day_out[i]),
            "date_unregistration":  None if ud == -1 else ud,
            "assessments":          student_assessments,
            "weekly_clicks":        [int(v) for v in clicks_mat[i]],
            "decayed_engagement":   [round(float(v), 4) for v in decayed_mat[i]],
            "risk_by_week":         _traj(risk_mat[i]),
            "tier_by_week":         [None if math.isnan(float(v)) else int(v) for v in tier_mat[i]],
            "lstm_trajectories": {
                hz: _traj(traj_mats[h][i]) for h, hz in enumerate(LSTM_HORIZONS)
            },
        })

    return key, {
        "module":             mod,
        "presentation":       pres,
        "num_weeks":          T,
        "cohort_p75_decayed": [round(float(v), 4) for v in p75],
        "students":           processed_students,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load all CSV tables
    print("\n🔄 Loading OULAD tables…")
    for name in ("courses.csv", "studentInfo.csv", "studentRegistration.csv",
                 "assessments.csv", "studentAssessment.csv", "studentVle.csv"):
        csv_path(name)   # fail fast if any file is missing

    courses_df  = pd.read_csv(csv_path("courses.csv"))
    info_df     = pd.read_csv(csv_path("studentInfo.csv"))
    reg_df      = pd.read_csv(csv_path("studentRegistration.csv"))
    assess_df   = pd.read_csv(csv_path("assessments.csv"))
    stu_ass_df  = pd.read_csv(csv_path("studentAssessment.csv"))

    # Load LSTM trajectory table
    lstm_by_course: dict[str, list[dict]] = {}
    traj_cols = ["id_student", "week"] + [f"risk_{hz}" for hz in LSTM_HORIZONS]
    if LSTM_TRAJ_CSV.exists():
        lstm_df = pd.read_csv(LSTM_TRAJ_CSV, usecols=["code_module", "code_presentation"] + traj_cols)
        for (mod, pres), grp in lstm_df.groupby(["code_module", "code_presentation"]):
            lstm_by_course[f"{mod}_{pres}"] = grp[traj_cols].to_dict("records")
        print(f"  → Loaded {len(lstm_df):,} LSTM trajectory rows across {len(lstm_by_course)} courses")
    else:
        print(f"  ⚠️  {LSTM_TRAJ_CSV.name} not found — using heuristic risk for all courses")

    # VLE: single vectorised groupby (replaces chunk streaming loop)
    print("  Aggregating studentVle.csv…", flush=True)
    vle_raw = pd.read_csv(csv_path("studentVle.csv"))
    vle_raw = vle_raw[vle_raw["date"] > 0].copy()
    vle_raw["week"] = ((vle_raw["date"] - 1) // 7).astype(np.int32)
    vle_weekly = (
        vle_raw
        .groupby(["code_module", "code_presentation", "id_student", "week"], sort=False)["sum_click"]
        .sum()
        .reset_index()
        .rename(columns={"sum_click": "clicks"})
    )
    del vle_raw
    print(f"    → {len(vle_weekly):,} weekly VLE records")

    # Build per-course bundles (pre-filtered slices → cheap to pickle)
    print(f"\n⚙️  Building {len(courses_df)} course bundles…")
    bundles: list[dict] = []

    for _, crow in courses_df.iterrows():
        mod  = str(crow["code_module"])
        pres = str(crow["code_presentation"])
        T    = math.ceil(int(crow["module_presentation_length"]) / 7)

        stu = info_df[(info_df["code_module"] == mod) & (info_df["code_presentation"] == pres)]
        if stu.empty:
            continue

        sids  = set(stu["id_student"].tolist())
        ameta = assess_df[(assess_df["code_module"] == mod) & (assess_df["code_presentation"] == pres)]
        aids  = set(ameta["id_assessment"].tolist())

        bundles.append({
            "mod":         mod,
            "pres":        pres,
            "num_weeks":   T,
            "students":    stu.to_dict("records"),
            "regs":        reg_df[
                               (reg_df["code_module"] == mod) &
                               (reg_df["code_presentation"] == pres)
                           ][["id_student", "date_registration", "date_unregistration"]].to_dict("records"),
            "assess_meta": ameta.to_dict("records"),
            "vle":         vle_weekly[
                               (vle_weekly["code_module"] == mod) &
                               (vle_weekly["code_presentation"] == pres)
                           ][["id_student", "week", "clicks"]].to_dict("records"),
            "scores":      stu_ass_df[
                               stu_ass_df["id_student"].isin(sids) &
                               stu_ass_df["id_assessment"].isin(aids)
                           ][["id_student", "id_assessment", "score", "date_submitted"]].to_dict("records"),
            "lstm_risks":  lstm_by_course.get(f"{mod}_{pres}", []),
        })

    # Process all courses in parallel
    n_workers = max(1, min(len(bundles), os.cpu_count() or 1))
    print(f"\n🚀 Processing {len(bundles)} courses across {n_workers} workers…\n")

    index_courses: list[dict] = []

    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        futures = {pool.submit(process_course, b): f"{b['mod']}_{b['pres']}" for b in bundles}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Courses"):
            course_key, output = future.result()
            if output is None:
                continue

            out_path = OUT_DIR / f"{course_key}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(output, f, separators=(",", ":"))

            n_stu = len(output["students"])
            tqdm.write(f"  ✓ {course_key}: {n_stu} students")
            index_courses.append({
                "module":        output["module"],
                "presentation":  output["presentation"],
                "num_weeks":     output["num_weeks"],
                "student_count": n_stu,
            })

    with open(OUT_DIR / "index.json", "w", encoding="utf-8") as f:
        json.dump({"courses": index_courses}, f, indent=2)

    print(f"\n✅ Done. Output in {OUT_DIR}")
