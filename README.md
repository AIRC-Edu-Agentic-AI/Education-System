# Student Agent

Flutter + FastAPI + MongoDB Atlas + LM Studio (local LLM)

An AI-powered student learning assistant with a multi-agent backend. The system observes student data (VLE engagement, assessments, knowledge state) and autonomously takes actions — updating study plans, sending notifications, and providing personalised guidance through chat.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Mobile | Flutter 3.x, Riverpod, GoRouter |
| Backend | FastAPI, Python 3.13, APScheduler |
| AI / Agents | LangChain 1.x, LangGraph, LM Studio (local LLM) |
| Database | MongoDB Atlas |
| Auth | Auth0 (placeholder) / demo token |

---

## Architecture Overview

```
Flutter App
  └── ApiService (Dio) ──► FastAPI backend (port 8000)
                                │
                    ┌───────────┼───────────────┐
                    │           │               │
              Routers       Scheduler       Agent Package
            /chat/stream   APScheduler      agent/
            /student        every 15min      base.py (14 tools)
            /assignments    daily 08:00      orchestrators/
            /notify         weekly Mon       specialists/
                            Sunday 20:00
                                │
                        LM Studio (local LLM)
                        http://127.0.0.1:1234
```

### Two-Phase Chat

Every chat request runs two agents in sequence:

1. **Proactive Phase** (max 3 iterations) — silent background check: inspects assignments and schedule, takes one write action if urgent (creates reminder or updates study plan). No content streamed to user.
2. **Q&A Phase** (max 5 iterations) — answers the user's message. System prompt is selected by LLM-based intent classification.

### Intent Classification

Before the Q&A phase, a single non-streaming LLM call classifies the message into one of five intents, each with a tailored system prompt:

| Intent | Example trigger | Agent behaviour |
|---|---|---|
| `tutoring` | "giải thích hồi quy tuyến tính" | Teaches concept + calls `update_knowledge_state` |
| `performance` | "kết quả học tập của tôi" | Chains profile + KT + assignments into analysis |
| `recommendation` | "nên học môn gì tiếp theo" | Calls `get_course_recommendations`, prereq gap advice |
| `wellbeing` | "tôi đang căng thẳng" | Empathetic response + reads study plan for relief |
| `general` | everything else | Standard Q&A assistant |

---

## Agent System (Phases 1–6)

### Tools (14 total)

All tools are created via `make_tools(student_id)` — `student_id` is pre-bound so the LLM never needs to pass it.

**Read tools**
| Tool | Returns |
|---|---|
| `get_student_profile` | Full profile, VLE summary, risk, prerequisite gaps |
| `get_assignments` | All assessments with scores, due dates, submission status |
| `get_schedule` | Weekly timetable with urgency flags |
| `get_study_plan` | SM-2 spaced repetition sessions |
| `get_knowledge_state` | Per-concept mastery probabilities (0.0–1.0) |
| `get_resources` | Learning resources, optionally filtered by topic |
| `get_assignment_milestones` | Milestone list for a specific assessment |
| `get_course_recommendations` | Ready/not-ready courses based on mastery thresholds |

**Write tools** (each emits `data_updated` SSE → Flutter invalidates the relevant provider)
| Tool | Effect | Provider invalidated |
|---|---|---|
| `update_study_plan` | Upserts `study_plans` collection | `studyPlanProvider` |
| `create_reminder` | Inserts into `notifications` | `notificationProvider` |
| `mark_assignment_complete` | Sets `submitted_date` on assessment | `studentProvider` |
| `save_study_note` | Inserts into `resources` | `resourcesProvider` |
| `update_knowledge_state` | Updates mastery with Bayesian EMA rule | `knowledgeStateProvider` |
| `break_down_assignment` | Stores agent-generated milestones | `assignmentMilestonesProvider` |
| `update_milestone_status` | Updates single milestone status | `assignmentMilestonesProvider` |

### Specialist Agents

| File | Purpose | Trigger |
|---|---|---|
| `agent/event_checker.py` | Rule-based: checks deadlines, VLE, risk, milestones | Scheduler every 15 min |
| `agent/daily_planner.py` | Rebuilds today's study sessions | Cron 08:00 daily |
| `agent/weekly_planner.py` | Rebuilds full Mon–Sun schedule | Cron Monday 08:05 + dynamic |
| `agent/course_planner.py` | Semester-level trajectory advice | Assessment shock / midpoint |
| `agent/performance_analysis.py` | O3: KT + VLE + scores synthesis | Chat intent / O1 |
| `agent/progress_report.py` | Weekly accomplishments summary | Cron Sunday 20:00 |
| `agent/student_skills.py` | KT gateway: read/write mastery | Post-tutoring / O1 |
| `agent/resource_curation.py` | Finds resources for weak concepts | O3 |
| `agent/assignment_breakdown.py` | Generates milestones from assignment | On-demand from enrollment screen |
| `agent/course_recommendation.py` | Rule-based prereq mastery check | Chat recommendation intent / O2 |
| `agent/wellbeing.py` | Empathetic notification + schedule relief | Risk > 0.8 / VLE > 7 days |

### Orchestrators

| File | Purpose | Sequence |
|---|---|---|
| `orchestrators/risk_intervention.py` | **O1** — full intervention chain | O3 → Course Planning → Weekly Planning → summary notification |
| `orchestrators/course_planning.py` | **O2** — course-level orchestration | Skill gaps → Course Recommendation → Course Planner → guidance notification |

### Dynamic Trigger Chain (Event Checker)

```
event_check (every 15 min)
  ├── deadline ≤ 3 days          → deadline_warning notification
  ├── assessment score < 50%     → assessment_shock notification + O2
  ├── VLE inactivity > 3 days    → vle_inactivity notification
  ├── VLE inactivity > 7 days    → Wellbeing Agent
  ├── milestone past due         → milestone_check notification (with action chips)
  ├── risk_score > 0.7           → O1 Risk Intervention
  │     ├── O3 Performance Analysis (KT + VLE + scores → study note)
  │     ├── Course Planning Agent (semester advice)
  │     ├── Weekly Planning Agent (rebuild schedule)
  │     └── summary intervention notification
  └── risk_score > 0.8           → Wellbeing Agent
```

---

## Database

### MongoDB Atlas Collections

| Collection | Contents |
|---|---|
| `students` | Profile, enrollments, assessments, VLE summary, risk score/flags |
| `timetable_blocks` | Weekly schedule per student |
| `study_plans` | SM-2 study sessions (rebuilt by planning agents) |
| `knowledge_states` | Per-concept mastery probabilities |
| `assignment_milestones` | Agent-generated milestones per assessment |
| `notifications` | All notifications with `action_options` for tappable chips |
| `resources` | Learning resources + agent-saved study notes |

### Knowledge Tracing Model

Mastery is updated using a weighted exponential moving average:

```
new_mastery = current + w × (observed_score − current)
```

Evidence weights: `assignment=0.4`, `quiz=0.3`, `tutor_interaction=0.2`, `self_report=0.1`

### Seeding for Demo

Populates all collections with data tuned to trigger every agentic behaviour:

```bash
cd backend
python -W ignore db/seed.py
```

Expected triggers from a single `POST /debug/trigger/event_check`:
1. `deadline_warning` — TMA-02 due in 3 days
2. `assessment_shock` — TMA-01 score 42% → O2 Course Planning
3. `vle_inactivity` — 4 days inactive
4. `milestone_check` ×2 — two overdue milestones
5. O1 Risk Intervention — risk 0.82 → O3 + Course Planner + Weekly Planner
6. Wellbeing — risk 0.82 > 0.8 threshold

---

## Setup

### Prerequisites

- Flutter SDK 3.x
- Python 3.11+
- [LM Studio](https://lmstudio.ai) with a model loaded and local server running on port 1234
- MongoDB Atlas account (free tier is sufficient)

### Backend

```bash
cd student_app/backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

# Copy and fill in the env file
cp .env.example .env
# Edit .env: set MONGODB_URI and LM_STUDIO_MODEL

# Seed the database
python -W ignore db/seed.py

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Flutter App

```bash
cd student_app

# Copy and fill in the env file
cp .env.example .env
# Edit .env: set API_BASE_URL to your backend IP

flutter pub get
flutter run
```

### LM Studio

1. Load a model (tested with `qwen/qwen3.5-9b`)
2. Start the local server on port 1234
3. Set `LM_STUDIO_MODEL` in `backend/.env` to match the model identifier shown in LM Studio

The backend supports both Qwen3 (`<think>` tag reasoning) and DeepSeek-R1 (`reasoning_content` field) automatically.

---

## Environment Variables

### `backend/.env`

```
MONGODB_URI=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net
MONGODB_DB=student_agent_db
USE_MOCK_DATA=false
LM_STUDIO_BASE_URL=http://127.0.0.1:1234/api/v1
LM_STUDIO_MODEL=qwen/qwen3.5-9b
ENVIRONMENT=demo
```

### `student_app/.env`

```
API_BASE_URL=http://localhost:8000
USE_MOCK_DATA=false
POLLING_INTERVAL_SECONDS=30
```

See `.env.example` files for full variable lists.

---

## Mock Fallback

The app degrades gracefully at every layer:

| Condition | Behaviour |
|---|---|
| `USE_MOCK_DATA=true` | Backend always uses `db/mock_data.py` |
| MongoDB unreachable | Backend falls back to `db/mock_data.py` |
| Backend unreachable | Flutter `ApiService` switches to `MockData.*` |
| LM Studio unreachable | Chat returns `ConnectError` SSE event |
| Intent classification fails | Falls back to keyword-based `_detect_intent()` |
| Write tool called in mock mode | Returns `{"status": "mock_mode"}` no-op |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/login` | Demo login — any password for seeded student_id |
| `GET` | `/student/{id}` | Student profile |
| `GET` | `/student/{id}/knowledge` | Per-concept mastery states |
| `POST` | `/chat/stream` | SSE streaming chat (two-phase agent) |
| `GET` | `/schedule/{id}/weekly` | Weekly timetable |
| `GET` | `/schedule/{id}/plan` | Study plan sessions |
| `GET` | `/notify/{id}` | Notifications (with action_options) |
| `PATCH` | `/notify/{id}/read` | Mark notification read |
| `GET` | `/assignments/{id}/milestones` | Milestone list for assessment |
| `POST` | `/assignments/{id}/breakdown` | Trigger agent milestone generation |
| `PATCH` | `/assignments/milestone/status` | Update milestone status |
| `GET` | `/health` | Backend + DB status |
| `POST` | `/debug/trigger/{job_id}` | Manually fire a scheduler job (dev only) |

### Scheduler Jobs

| Job ID | Schedule | Agent |
|---|---|---|
| `event_check` | Every 15 min | Event Checker → cascade triggers |
| `daily_plan` | Daily 08:00 | Daily Planner |
| `weekly_plan` | Monday 08:05 | Weekly Planner |
| `progress_report` | Sunday 20:00 | Progress Report |

---

## File Structure

```
student_app/
├── .env                          # Flutter env (gitignored)
├── .env.example
├── lib/
│   ├── core/
│   │   ├── config/env_config.dart
│   │   ├── theme/app_theme.dart
│   │   └── router/app_router.dart
│   ├── data/
│   │   ├── mock/mock_data.dart
│   │   └── services/api_service.dart
│   ├── models/
│   │   ├── student_model.dart         # StudentModel, NotificationModel, etc.
│   │   ├── chat_message_model.dart    # ChatMessage, ToolCallInfo, kToolDisplayLabels
│   │   └── assignment_milestone_model.dart
│   ├── providers/providers.dart       # All Riverpod providers
│   └── screens/
│       ├── dashboard/                 # Notifications with action chips
│       ├── chat/                      # Streaming chat + tool chips + thinking traces
│       ├── my_enrollment/             # Assessments + milestone cards
│       └── profile/                   # Profile + knowledge mastery bars
│
backend/
├── .env                          # Backend env (gitignored)
├── .env.example
├── main.py                       # FastAPI app + lifespan scheduler
├── requirements.txt
├── scheduler.py                  # APScheduler job definitions
├── db/
│   ├── mongodb.py                # Atlas connection with mock fallback
│   ├── mock_data.py              # OULAD-shaped demo data
│   └── seed.py                   # Demo database seeder
├── routers/
│   ├── chat.py                   # Two-phase streaming agent endpoint
│   ├── student.py
│   ├── assignments.py
│   ├── schedule.py
│   ├── notifications.py
│   └── auth.py
└── agent/
    ├── base.py                   # 14 tools, KT update rule, intent detection
    ├── student_skills.py         # KT read/write gateway
    ├── event_checker.py          # Rule-based trigger engine
    ├── daily_planner.py
    ├── weekly_planner.py
    ├── course_planner.py
    ├── performance_analysis.py   # Orchestrator O3
    ├── progress_report.py
    ├── assignment_breakdown.py
    ├── course_recommendation.py
    ├── wellbeing.py
    ├── resource_curation.py
    └── orchestrators/
        ├── risk_intervention.py  # O1
        └── course_planning.py    # O2
```

---

## SSE Event Types

The `/chat/stream` endpoint emits newline-delimited Server-Sent Events:

| Type | Payload | Description |
|---|---|---|
| `tool_call` | `{name}` | Agent is calling a tool |
| `thinking` | `{delta}` | LLM reasoning token (DeepSeek/Qwen3) |
| `thinking_done` | — | Reasoning phase complete |
| `content` | `{delta}` | Response text token |
| `data_updated` | `{resources[]}` | Write tool fired; Flutter invalidates providers |
| `done` | — | Response complete |
| `error` | `{message}` | Error occurred |
