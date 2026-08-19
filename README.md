# Education System — Agentic Multi-Agent Personalized Tiered Learning Support

An end-to-end AI-powered education ecosystem with a multi-agent backend, tiered learning analytics (RTI/MTSS), a Flutter mobile assistant for students, and a React analytics dashboard for teachers.

---

## Architecture

```
education-system/
├── backend/                       ← FastAPI + LangChain + Multi-Agent Engine (:8000)
│   ├── agent/                     ← 14 Read/Write Tools, LLM Pool, Specialists & Orchestrators
│   ├── routers/                   ← REST & WebSocket APIs (Auth, Student, Teacher, Chat, Risk)
│   ├── scheduler.py               ← APScheduler background jobs (15min event check, daily/weekly plans)
│   └── db/                        ← Async MongoDB (Motor) & PostgreSQL Event Logging
├── teacher-dashboard/             ← React 18 + Vite + TypeScript + Material-UI (:5173)
│   ├── src/adapters/              ← Swap point: ProcessedDataAdapter ↔ ApiDataAdapter
│   ├── src/modules/               ← Feature modules (Dashboard, Student, Class, Schedule, Auth)
│   └── src/di/container.ts        ← Dependency Injection container
└── student-app/                   ← Flutter 3.x + Riverpod + GoRouter (Mobile / Web)
    ├── lib/data/                  ← Dio API clients & Repositories
    ├── lib/providers/             ← Riverpod state management (auto-invalidated by SSE events)
    └── lib/screens/               ← Student views (Chat AI, Timetable, Study Plan, Groups, Analytics)
```

**Data & Event Flow**:
- **Student App** $\longleftrightarrow$ **FastAPI Backend** via HTTP REST, Server-Sent Events (`/chat/stream`) and WebSocket (`/realtime-chat`).
- **Teacher Dashboard** $\longleftrightarrow$ **FastAPI Backend** with Auth0 authentication for RTI/MTSS cohort analytics and interventions.
- **LLM Pool Router** directs requests to local LM Studio (e.g. `qwen/qwen3.5-9b`) with automatic cloud fallback to **Anthropic Claude**.

---

## Setup

### 1. Prerequisites

- **Python**: 3.11 or 3.13 (`python --version`)
- **Node.js**: v20+ (`node -v`)
- **Flutter SDK**: 3.x+ (`flutter --version`) *(optional for mobile)*
- **MongoDB**: MongoDB Atlas URI or local MongoDB instance
- **LM Studio**: Running on `http://127.0.0.1:1234` *(or provide Anthropic API key)*

---

### 2. Backend Setup

```bash
cd backend

# Create & activate virtual environment
python -m venv venv
.\venv\Scripts\activate            # Windows
# source venv/bin/activate         # Linux / macOS

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env -> set MONGODB_URI, LM_STUDIO_MODEL or ANTHROPIC_API_KEY

# Seed initial data (optional)
python scripts/enrich_database.py

# Start FastAPI server
uvicorn main:app --reload --port 8000
```

Verify: Open `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/health`.

---

### 3. Teacher Dashboard Setup

```bash
cd teacher-dashboard

# Install dependencies
npm install

# Configure environment
cp .env.example .env

# Start development server
npm run dev
```

Verify: Open `http://localhost:5173` in your browser.

---

### 4. Student App Setup (Flutter)

```bash
cd student-app

# Configure environment
cp .env.example .env
# Edit .env -> set API_BASE_URL=http://localhost:8000

# Install dependencies
flutter pub get

# Launch on Chrome or connected device
flutter run -d windows
```

---

## Views & Interfaces

### Teacher Dashboard (`/teacher-dashboard`)

| View | Path | Description |
|---|---|---|
| Class Overview | `/` | RTI/MTSS tier distribution chart, risk tiles, student cohort table |
| Student Detail | `/student/:id` | Risk trajectory, VLE activity, assessment scores, prerequisite mastery |
| Teaching Schedule | `/schedule` | Timetable blocks, teaching hours, classroom assignments |
| Class Management | `/class` | Classroom roster, notification broadcaster, student intervention manager |

### Student Mobile App (`/student-app`)

| View | Route | Description |
|---|---|---|
| Dashboard | `/dashboard` | Daily progress, upcoming deadlines, knowledge mastery radar |
| AI Tutor Chat | `/chat` | Two-phase streaming agent with 5 dynamic intents & proactive reminders |
| Timetable | `/timetable` | Weekly schedule with priority flags & event triggers |
| Study Plan | `/study-plan` | SM-2 spaced repetition review sessions with self-rating |
| Assignments | `/my-enrollment` | Assessment submission, automated AI milestone breakdown |
| Study Groups | `/study-groups` | Smart peer study groups and real-time class channel discussions |

---

## Multi-Agent AI System

### Two-Phase Chat Engine

```
User Message
     │
     ▼
[ Phase 1: Proactive Agent ] ──► (Silent check: deadlines, risk, schedule)
     │                           └── Performs 1 write action if urgent (e.g. create reminder)
     ▼
[ Intent Classifier ]        ──► Classifies into 1 of 5 intents (tutoring, performance, etc.)
     │
     ▼
[ Phase 2: Q&A Agent ]       ──► Streams tailored answer via SSE + executes tools
```

### Agent Tools (14 Tools with SSE Cache Invalidation)

| Category | Tool | Action / Invalidation |
|---|---|---|
| **Read** | `get_student_profile` | Full profile, risk score, VLE engagement summary |
| | `get_assignments` | Assessment list, grades, due dates |
| | `get_schedule` | Timetable blocks with urgency markers |
| | `get_study_plan` | SM-2 spaced repetition sessions |
| | `get_knowledge_state` | Concept mastery probabilities ($0.0 - 1.0$) |
| | `get_resources` | Curated learning materials by topic |
| | `get_assignment_milestones` | Sub-milestones for large assignments |
| | `get_course_recommendations` | Readiness advice based on prerequisite mastery |
| **Write** | `update_study_plan` | Upserts `study_plans` $\rightarrow$ invalidates `studyPlanProvider` |
| | `create_reminder` | Inserts `notifications` $\rightarrow$ invalidates `notificationProvider` |
| | `mark_assignment_complete` | Marks assessment submitted $\rightarrow$ invalidates `studentProvider` |
| | `save_study_note` | Stores notes into `resources` $\rightarrow$ invalidates `resourcesProvider` |
| | `update_knowledge_state` | Updates mastery via Bayesian EMA $\rightarrow$ invalidates `knowledgeStateProvider` |
| | `break_down_assignment` | Generates sub-milestones $\rightarrow$ invalidates `assignmentMilestonesProvider` |
| | `update_milestone_status` | Updates milestone progress $\rightarrow$ invalidates `assignmentMilestonesProvider` |

---

## Risk Model (RTI/MTSS Learning Analytics)

```
risk = 1 − (0.45 × assessment_performance + 0.35 × VLE_engagement + 0.20 × submission_rate)

Tier 1 (Universal / Low Risk)    risk < 0.33   → Standard learning path
Tier 2 (Targeted / Moderate)     0.33 ≤ risk < 0.66 → Automated SM-2 reminders & resource suggestions
Tier 3 (Intensive / High Risk)   risk ≥ 0.66   → O1 Risk Intervention Orchestrator & Teacher Alert
```

- **VLE engagement** is normalised against the cohort's 75th percentile cumulative clicks.
- **Event Checker** (`scheduler.py`) evaluates student risk every 15 minutes and triggers automated interventions.

---

## Extending

### Adding a new Agent Tool
1. Define the tool function in `backend/agent/base.py` with `@tool` decorator.
2. Add the tool to `make_tools(student_id)` list.
3. If it modifies state, ensure it returns a message and emits the corresponding SSE event.

### Adding a new Teacher Dashboard Module
1. Create `teacher-dashboard/src/modules/yourmodule/views/YourView.tsx`.
2. Add route in `teacher-dashboard/src/App.tsx`.
3. Connect components using DI container in `src/di/container.ts`.

### Adding a new Student App Screen
1. Create screen in `student-app/lib/screens/your_feature/`.
2. Register route in `student-app/lib/core/router/app_router.dart`.
3. Bind state with Riverpod providers in `student-app/lib/providers/`.

---

## Project Notes & Principles

- **Walking Skeleton Architecture**: All 3 tiers (Backend, Mobile, Web) are connected end-to-end. Extend by adding adapters and views without breaking contracts.
- **Local-First AI with Cloud Fallback**: Defaults to local LM Studio inference for zero cloud cost and low latency, falling back to Claude for resilience.
- **Reactive UI**: State across Flutter and React dashboards updates automatically upon Agent actions via SSE data events and WebSocket change streams.
