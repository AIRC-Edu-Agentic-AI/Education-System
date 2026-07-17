# Teacher Dashboard — RTI/MTSS Learning Analytics

Pilot prototype for the Agentic Multi-Agent System for Personalized Tiered Learning Support dissertation project.
Built on the OULAD (Open University Learning Analytics Dataset).

---

## Architecture

```
src/
├── adapters/          ← Swap point: mock ↔ real backend
│   ├── ProcessedDataAdapter.ts    (reads preprocessed JSON)
│   ├── MockMasteryAdapter.ts      (concept graph mock — replace with Neo4j G_course)
│   └── ClaudeAgentAdapter.ts      (streams from Anthropic API via Vite proxy)
├── di/container.ts    ← Only file that changes between phases
├── modules/           ← Feature modules (Dashboard, Student, Chat, Mastery)
├── ports/             ← Interfaces (DataService, AgentService, MasteryService)
└── shared/            ← Zustand stores, Shell, Event bus
```

**Phase progression** — edit only `src/di/container.ts`:
- Modular: MockDataAdapter + MockAgentAdapter
- Pilot (current): ProcessedDataAdapter + ClaudeAgentAdapter
- Deploy: ApiDataAdapter + ClaudeAgentAdapter

---

## Setup

### 1. Install Node.js 20

**Windows / macOS:** download the LTS installer from https://nodejs.org

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```
Verify: `node -v` should print `v20.x.x`

### 2. Install project dependencies

```bash
cd teacher-dashboard
npm install
```

All packages are listed in `requirements.txt` and `package.json`.
Expected time: ~30 seconds.

### 3. Place OULAD CSV files

Download (free, registration required): https://analyse.kmi.open.ac.uk/open_dataset

Place all 7 files in `public/data/oulad/`:
```
courses.csv  studentInfo.csv  studentRegistration.csv
studentVle.csv  studentAssessment.csv  assessments.csv  vle.csv
```

### 4. Add your Anthropic API key

```bash
cp .env.example .env
# Edit .env → set ANTHROPIC_API_KEY=sk-ant-...
```

Key is used only by the Vite dev-server proxy — never bundled into the browser.
Get a key at https://console.anthropic.com

### 5. Preprocess the data

Install Python dependencies (one-time):
```bash
pip install -r scripts/python/requirements.txt
```

Then run:
```bash
npm run preprocess
# internally calls: python scripts/python/preprocess.py
```

Reads the 7 CSVs with chunked streaming (constant memory regardless of file size), computes per-student per-week risk scores, writes JSON to `public/processed/`.
Expected time: 3–8 minutes for the full dataset (~32 000 students). Progress bars show per-file and per-course status.

### 6. Start

```bash
npm run dev
# Open http://localhost:5173
```

---

## Views

| View | Path | Description |
|---|---|---|
| Class Overview | `/` | Module/presentation/week selector, risk tiles, tier distribution chart, student table |
| Student Detail | `/student/:id` | Demographics, risk trajectory, VLE activity, assessment scores |
| Concept Mastery | `/mastery` | D3 force-directed concept graph (mock data, see adapter note) |
| AI Advisor | `/chat` | Streaming chat with Claude, context-injected from current view |

---

## Risk model

```
risk = 1 − (0.45 × assessment_performance + 0.35 × VLE_engagement + 0.20 × submission_rate)

Tier 1 (low risk)    risk < 0.33
Tier 2 (moderate)    0.33 ≤ risk < 0.66
Tier 3 (high risk)   risk ≥ 0.66
```

VLE engagement is normalised against the cohort's 75th percentile cumulative clicks at each week.

---

## Extending

### Adding a new feature module
1. Create `src/modules/yourmodule/views/YourView.tsx`
2. Add one entry to `src/modules/registry.ts`
3. Add a `<Route>` in `src/App.tsx`

### Replacing the mastery mock with Neo4j
1. Implement `src/adapters/Neo4jMasteryAdapter.ts` conforming to `MasteryService`
2. In `src/di/container.ts`, replace `new MockMasteryAdapter()` with `new Neo4jMasteryAdapter()`

### Adding a real XGBoost risk model
The preprocessing script (`scripts/preprocess.ts`) is the insertion point.
Replace the `computeRisk()` heuristic with a call to your trained model endpoint,
or add a Python preprocessing step that outputs the same JSON schema.

---

## Intern team notes

- **Tech Lead** (4th year, France): review this architecture doc, own the DI container and adapter interfaces
- **4th year local**: own Dashboard module + preprocessing script extensions
- **3rd year**: own Student Detail view + assessment data pipeline
- **2nd year**: own Chat module UI + message history persistence

**Walking Skeleton** principle: every layer is wired end-to-end now.
Build features by filling in adapters and expanding views — never break the DI contract.
