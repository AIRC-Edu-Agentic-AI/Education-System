from __future__ import annotations
import math
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd
from pymongo import MongoClient
from tqdm import tqdm

ROOT    = Path(__file__).resolve().parents[2]
CSV_DIR = ROOT / "public" / "data" / "oulad"

ATLAS_URI = "mongodb+srv://whitedevil0981907116_db_user:airc@ouladcluster.tsrzoux.mongodb.net/?appName=OuladCluster"
DECAY_LAMBDA = 0.15

def build_decay_matrix(n):
    t = np.arange(n, dtype=np.float32)
    return np.tril(np.exp(-DECAY_LAMBDA * (t[:, None] - t[None, :])))

def process_course(bundle):
    mod  = bundle["mod"]
    pres = bundle["pres"]
    T    = bundle["num_weeks"]
    key  = f"{mod}_{pres}"

    students_df    = pd.DataFrame(bundle["students"])
    regs_df        = pd.DataFrame(bundle["regs"])
    assess_meta_df = pd.DataFrame(bundle["assess_meta"])
    vle_df         = pd.DataFrame(bundle["vle"])
    scores_df      = pd.DataFrame(bundle["scores"])

    if students_df.empty:
        return key, None

    # Clean numeric columns
    if not assess_meta_df.empty:
        assess_meta_df["date"]   = pd.to_numeric(assess_meta_df["date"],   errors="coerce")
        assess_meta_df["weight"] = pd.to_numeric(assess_meta_df["weight"], errors="coerce")
    if not scores_df.empty:
        scores_df["score"]          = pd.to_numeric(scores_df["score"],          errors="coerce")
        scores_df["date_submitted"] = pd.to_numeric(scores_df["date_submitted"], errors="coerce")
    if not regs_df.empty:
        regs_df["date_registration"]   = pd.to_numeric(regs_df["date_registration"],   errors="coerce")
        regs_df["date_unregistration"] = pd.to_numeric(regs_df["date_unregistration"], errors="coerce")

    student_ids = students_df["id_student"].to_numpy(dtype=np.int64)
    S = len(student_ids)
    sid_idx = {int(s): i for i, s in enumerate(student_ids)}

    # Weekly clicks matrix
    clicks_mat = np.zeros((S, T), dtype=np.float32)
    if not vle_df.empty:
        v = vle_df.copy()
        v["sidx"] = v["id_student"].map(sid_idx)
        v = v.dropna(subset=["sidx"])
        v["sidx"] = v["sidx"].astype(np.int32)
        v = v[(v["week"] >= 0) & (v["week"] < T)]
        np.add.at(clicks_mat, (v["sidx"].to_numpy(), v["week"].to_numpy(dtype=np.int32)), v["clicks"].to_numpy(dtype=np.float32))

    # Decayed engagement
    decayed_mat = clicks_mat @ build_decay_matrix(T).T
    p75 = np.maximum(np.percentile(decayed_mat, 75, axis=0), 5.0)

    # Registration mask
    reg_day   = np.zeros(S, dtype=np.float32)
    unreg_day = np.full(S, np.inf, dtype=np.float32)
    if not regs_df.empty:
        regs_idx = regs_df.set_index("id_student")
        for i, sid in enumerate(student_ids):
            if sid in regs_idx.index:
                row = regs_idx.loc[sid]
                rd, ud = row["date_registration"], row["date_unregistration"]
                if not pd.isna(rd): reg_day[i] = float(rd)
                if not pd.isna(ud): unreg_day[i] = float(ud)

    current_days = (np.arange(T, dtype=np.float32) + 1) * 7
    active = (reg_day[:, None] <= current_days[None, :]) & (unreg_day[:, None] >= current_days[None, :])

    # Assessment matrices
    A = len(assess_meta_df)
    has_assess = A > 0
    if has_assess:
        aid_arr      = assess_meta_df["id_assessment"].to_numpy(dtype=np.int64)
        date_nan     = assess_meta_df["date"].isna().to_numpy()
        weight_nan   = assess_meta_df["weight"].isna().to_numpy()
        date_due     = np.where(date_nan,   np.inf, assess_meta_df["date"].to_numpy(dtype=np.float32))
        weight_vec   = np.where(weight_nan, 0.0,    assess_meta_df["weight"].to_numpy(dtype=np.float32))
        assess_types = assess_meta_df["assessment_type"].tolist()
        aid_idx      = {int(a): j for j, a in enumerate(aid_arr)}
        score_mat    = np.full((S, A), np.nan, dtype=np.float32)
        sub_day_mat  = np.full((S, A), np.nan, dtype=np.float32)

        if not scores_df.empty:
            sc = scores_df.copy()
            sc["sidx"] = sc["id_student"].map(sid_idx)
            sc["aidx"] = sc["id_assessment"].map(aid_idx)
            sc = sc.dropna(subset=["sidx", "aidx"])
            sc["sidx"] = sc["sidx"].astype(np.int32)
            sc["aidx"] = sc["aidx"].astype(np.int32)
            has_sc = ~sc["score"].isna()
            score_mat[sc.loc[has_sc, "sidx"].to_numpy(), sc.loc[has_sc, "aidx"].to_numpy()] = sc.loc[has_sc, "score"].to_numpy(dtype=np.float32)
            has_ds = ~sc["date_submitted"].isna()
            sub_day_mat[sc.loc[has_ds, "sidx"].to_numpy(), sc.loc[has_ds, "aidx"].to_numpy()] = sc.loc[has_ds, "date_submitted"].to_numpy(dtype=np.float32)

    # Risk & tier
    risk_mat = np.full((S, T), np.nan, dtype=np.float32)
    tier_mat = np.full((S, T), np.nan, dtype=np.float32)
    for w in range(T):
        active_w = active[:, w]
        if not active_w.any(): continue
        engagement = np.minimum(1.0, decayed_mat[:, w] / float(p75[w]))
        if has_assess:
            due_j = date_due <= current_days[w]
            n_due = int(due_j.sum())
        else:
            n_due = 0
        if n_due > 0:
            dw         = weight_vec * due_j
            total_dw   = float(dw.sum())
            ontime     = (~np.isnan(sub_day_mat)) & (sub_day_mat <= current_days[w])
            due_ontime = ontime & due_j[None, :]
            a_perf     = (np.where(due_ontime, score_mat / 100.0, 0.0) * dw[None, :]).sum(axis=1) / max(total_dw, 1e-9)
            sub_rate   = due_ontime.sum(axis=1) / n_due
        else:
            a_perf   = np.zeros(S, dtype=np.float32)
            sub_rate = np.zeros(S, dtype=np.float32)
        risk_w = np.round(np.clip(1.0 - (0.45 * a_perf + 0.35 * engagement + 0.20 * sub_rate), 0.0, 1.0), 4)
        tier_w = np.where(risk_w < 0.33, 1, np.where(risk_w < 0.66, 2, 3))
        risk_mat[active_w, w] = risk_w[active_w]
        tier_mat[active_w, w] = tier_w[active_w]

    reg_day_out   = reg_day.astype(np.int32)
    unreg_day_out = np.where(np.isinf(unreg_day), -1, unreg_day.astype(np.int32))

    processed_students = []
    for i, srow in enumerate(students_df.itertuples(index=False)):
        weekly = [int(v) for v in clicks_mat[i]]
        half   = T // 2

        clicks_per_month    = [int(sum(weekly[m:m+4])) for m in range(0, T, 4)]
        clicks_per_semester = [int(sum(weekly[:half])), int(sum(weekly[half:]))]

        student_assessments = []
        if has_assess:
            for j in range(A):
                student_assessments.append({
                    "id_assessment":   int(aid_arr[j]),
                    "assessment_type": assess_types[j],
                    "date_due":        None if date_nan[j] else int(date_due[j]),
                    "weight":          None if weight_nan[j] else float(weight_vec[j]),
                    "score":           None if np.isnan(score_mat[i, j]) else round(float(score_mat[i, j]), 2),
                    "date_submitted":  None if np.isnan(sub_day_mat[i, j]) else int(sub_day_mat[i, j]),
                })

        ud = int(unreg_day_out[i])
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
            "weekly_clicks":        weekly,
            "cumulative_clicks":    [int(v) for v in np.cumsum(clicks_mat[i])],
            "clicks_per_month":     clicks_per_month,
            "clicks_per_semester":  clicks_per_semester,
            "decayed_engagement":   [round(float(v), 4) for v in decayed_mat[i]],
            "risk_by_week":         [None if math.isnan(float(v)) else round(float(v), 4) for v in risk_mat[i]],
            "tier_by_week":         [None if math.isnan(float(v)) else int(v) for v in tier_mat[i]],
        })

    return key, {
        "module":             mod,
        "presentation":       pres,
        "num_weeks":          T,
        "cohort_p75_decayed": [round(float(v), 4) for v in p75],
        "students":           processed_students,
    }


if __name__ == "__main__":
    print("\n Connecting to raw cluster...")
    raw_client = MongoClient("mongodb+srv://micipssadjaroun_db_user:airc2@ouladcluster2.hvn6kza.mongodb.net/?appName=ouladcluster2")
    raw_db = raw_client["oulad_db"]

    print(" Loading data from Atlas raw...")
    courses_df  = pd.DataFrame(list(raw_db["modules"].find({}, {"_id": 0})))
    info_df     = pd.DataFrame(list(raw_db["students"].find({}, {"_id": 0})))
    reg_df      = pd.DataFrame(list(raw_db["registrations"].find({}, {"_id": 0})))
    assess_df   = pd.DataFrame(list(raw_db["assessments_meta"].find({}, {"_id": 0})))
    stu_ass_df  = pd.DataFrame(list(raw_db["student_assessments"].find({}, {"_id": 0})))

    print("  Aggregating vle_interactions from Atlas...")
    vle_raw = pd.DataFrame(list(raw_db["vle_interactions"].find({}, {"_id": 0})))
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

    # Rename columns to match expected format
    courses_df = courses_df.rename(columns={"code_module": "code_module", "code_presentation": "code_presentation", "module_presentation_length": "module_presentation_length"})

    print(f"\n Building {len(courses_df)} course bundles...")
    bundles = []
    for _, crow in courses_df.iterrows():
        mod  = str(crow["code_module"])
        pres = str(crow["code_presentation"])
        T    = math.ceil(int(crow["module_presentation_length"]) / 7)
        stu  = info_df[(info_df["code_module"] == mod) & (info_df["code_presentation"] == pres)]
        if stu.empty: continue
        sids  = set(stu["id_student"].tolist())
        ameta = assess_df[(assess_df["code_module"] == mod) & (assess_df["code_presentation"] == pres)]
        aids  = set(ameta["id_assessment"].tolist())
        bundles.append({
            "mod": mod, "pres": pres, "num_weeks": T,
            "students":    stu.to_dict("records"),
            "regs":        reg_df[(reg_df["code_module"] == mod) & (reg_df["code_presentation"] == pres)][["id_student", "date_registration", "date_unregistration"]].to_dict("records"),
            "assess_meta": ameta.to_dict("records"),
            "vle":         vle_weekly[(vle_weekly["code_module"] == mod) & (vle_weekly["code_presentation"] == pres)][["id_student", "week", "clicks"]].to_dict("records"),
            "scores":      stu_ass_df[stu_ass_df["id_student"].isin(sids) & stu_ass_df["id_assessment"].isin(aids)][["id_student", "id_assessment", "score", "date_submitted"]].to_dict("records"),
        })

    n_workers = max(1, min(len(bundles), os.cpu_count() or 1))
    print(f"\n Processing {len(bundles)} courses across {n_workers} workers...")

    processed_client = MongoClient(ATLAS_URI)
    db = processed_client["oulad_db"]
    db["processed_courses"].drop()
    db["processed_students"].drop()

    all_students = []

    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        futures = {pool.submit(process_course, b): f"{b['mod']}_{b['pres']}" for b in bundles}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Courses"):
            course_key, output = future.result()
            if output is None: continue
            db["processed_courses"].insert_one({
                "module":             output["module"],
                "presentation":       output["presentation"],
                "num_weeks":          output["num_weeks"],
                "cohort_p75_decayed": output["cohort_p75_decayed"],
                "student_count":      len(output["students"])
            })
            for s in output["students"]:
                s["code_module"]       = output["module"]
                s["code_presentation"] = output["presentation"]
                all_students.append(s)
            tqdm.write(f"  {course_key}: {len(output['students'])} students")

    if all_students:
        print(f"\n Inserting {len(all_students)} students...")
        batch_size = 500
        for i in range(0, len(all_students), batch_size):
            db["processed_students"].insert_many(all_students[i:i+batch_size])
            print(f"  Inserted {min(i+batch_size, len(all_students))}/{len(all_students)}")

    print(" Creating indexes...")
    db["processed_students"].create_index([("code_module", 1), ("code_presentation", 1)])
    db["processed_students"].create_index([("code_module", 1), ("code_presentation", 1), ("id_student", 1)])

    print(f"\n DONE ! Collections 'processed_courses' and 'processed_students' ready on Atlas.")