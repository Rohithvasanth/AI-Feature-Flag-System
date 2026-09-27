# 🚩 AI Feature Flag System — AI Expense Categorizer Demo

A production-grade, enterprise AI Feature Flag system built with **FastAPI**, **PostgreSQL**, **Redis**, **React**, **Recharts**, and **Tailwind CSS**.

This system enables safe, gradual releases of new AI models and feature versions, real-time quality monitoring, automated threshold violation alerts, automatic rollback triggers, non-intrusive shadow mode testing, and interactive dashboard control.

---

## 🌟 Key Features & Architecture

```
                                    ┌────────────────────────┐
                                    │    Client Request      │
                                    └───────────┬────────────┘
                                                │
                                                ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                FastAPI Backend Engine                                  │
│                                                                                        │
│  ┌───────────────────────────┐    ┌─────────────────────────┐    ┌──────────────────┐  │
│  │ Feature Flag Repository   │───►│ Consistent MD5 User     │───►│  Version Router  │  │
│  │ (Postgres / SQLite)       │    │ Hashing Bucket [0-100)  │    │  (v1 vs v2)      │  │
│  └───────────────────────────┘    └─────────────────────────┘    └────────┬─────────┘  │
│                                                                           │            │
│  ┌───────────────────────────┐    ┌─────────────────────────┐             │            │
│  │ Shadow Mode Execution     │◄───│ Quality Monitoring &    │◄────────────┴────────────┘  │
│  │ (Background Dual Eval)    │    │ Rollback Controller     │                            │
│  └───────────────────────────┘    └─────────────────────────┘                            │
└───────────────────────────────────────────────┬────────────────────────────────────────┘
                                                │
                                                ▼
                                    ┌────────────────────────┐
                                    │ React Dashboard & APIs │
                                    └────────────────────────┘
```

- **Consistent Hashing**: MD5 hashing of `user_id` + `feature_name` maps users deterministically to bucket ranges `[0.0, 100.0)` for repeatable experiment assignment.
- **Gradual Rollout Controller**: Gated staged progression (`0%` → `10%` → `25%` → `50%` → `75%` → `100%`) based on empirical AI quality metrics.
- **Automated Rollback Engine**: Real-time quality evaluation (`THRESHOLD_VIOLATED`) instantly resets `rollout_percentage` to `0.0%`, falling back to baseline `categorizer_v1`.
- **Non-Intrusive Shadow Mode**: Executes experiment version `categorizer_v2` in the background alongside production traffic, logging comparison accuracy and latency without affecting user responses.
- **Professional MLOps Dashboard**: Interactive single-page React app served at `GET /dashboard` showing real-time KPI cards, quality & rollout charts, audit logs, and live action buttons with safety modal confirmation.

---

## 📦 System Modules (Modules 1 – 14)

| Module | Title | Description |
| :--- | :--- | :--- |
| **Module 1** | **Setup & Architecture** | FastAPI app structure, Pydantic settings, `.env` support, health endpoints. |
| **Module 2** | **Basic Feature Flag Engine** | Feature flag data models, in-memory repository, evaluation logic. |
| **Module 3** | **Consistent User Assignment** | MD5 user hashing bucket algorithm `[0.0, 100.0)` for deterministic assignment. |
| **Module 4** | **PostgreSQL Database** | SQLAlchemy ORM integration with SQLite memory fallback for offline dev/tests. |
| **Module 5** | **FastAPI Backend REST APIs** | Full CRUD REST endpoints for feature flags and user evaluation. |
| **Module 6** | **Python SDK** | Production Python SDK client with context manager support and exception handling. |
| **Module 7** | **AI Expense Categorizer** | Demo baseline (`categorizer_v1`, rule-based) vs experiment (`categorizer_v2`, AI-enhanced). |
| **Module 8** | **Quality Evaluation** | Quality score formula `[0.0, 1.0]` combining accuracy, latency, and feedback. |
| **Module 9** | **Quality Monitoring** | Rolling quality trend health tracker (`STABLE`, `IMPROVING`, `DEGRADING`, `THRESHOLD_VIOLATED`). |
| **Module 10** | **Automatic Rollback** | Safety circuit-breaker reverting bad releases to 0.0% rollout upon threshold violation. |
| **Module 11** | **Gradual Rollout Controller**| Quality-gated staged rollout advancement with automatic rollback guardrails. |
| **Module 12** | **Professional Dashboard** | React + Recharts + Tailwind CSS web dashboard served live at `/dashboard`. |
| **Module 13** | **Shadow Mode** | Background evaluation of `categorizer_v2` without altering production outputs. |
| **Module 14** | **Testing, Docker & Final Demo**| End-to-end integration test suite, `Dockerfile`, `docker-compose.yml`, and documentation. |

---

## 🚀 Quick Start Guide

### Option 1: Docker Compose (Recommended for Production)

Run the backend, PostgreSQL database, and Redis cache together in Docker containers:

```bash
# Build and start all services (Backend + PostgreSQL + Redis)
docker-compose up --build -d

# Check running containers
docker-compose ps

# View backend logs
docker-compose logs -f backend

# Stop all services
docker-compose down -v
```

Services exposed:
- **FastAPI Application & Dashboard**: `http://localhost:8000/dashboard`
- **Interactive Swagger API Docs**: `http://localhost:8000/docs`
- **PostgreSQL Database**: `localhost:5432` (User: `postgres`, Pass: `postgres`, DB: `ai_feature_flags`)
- **Redis Cache**: `localhost:6379`

---

### Option 2: Local Python Environment

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run full pytest suite (46 tests)
python -m pytest -v

# 3. Start Uvicorn development server
python -m app.main
# or
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## 📡 REST API Reference

### 1. Feature Flags API
- `POST /api/v1/flags/` — Create new feature flag
- `GET /api/v1/flags/` — List all feature flags
- `GET /api/v1/flags/{feature_name}` — Get feature flag details
- `PUT /api/v1/flags/{feature_name}` — Update rollout %, status, or quality threshold
- `DELETE /api/v1/flags/{feature_name}` — Delete feature flag
- `POST /api/v1/flags/{feature_name}/evaluate` — Evaluate feature flag for a specific user ID

### 2. AI Expense Categorizer API
- `POST /api/v1/categorize` — Categorize expense (`description`, `amount`, `user_id`) using assigned AI version

### 3. Quality & Monitoring API
- `POST /api/v1/quality/evaluate` — Record quality evaluation log
- `GET /api/v1/quality/summary/{feature_name}` — Comparative quality summary (v1 vs v2)
- `GET /api/v1/monitoring/status/{feature_name}` — Real-time health status (`HEALTHY` vs `THRESHOLD_VIOLATED`)
- `POST /api/v1/monitoring/snapshot/{feature_name}` — Capture monitoring state snapshot

### 4. Automatic Rollback & Gradual Rollout API
- `POST /api/v1/rollback/evaluate/{feature_name}` — Trigger automatic rollback if threshold is violated
- `GET /api/v1/rollback/history/{feature_name}` — Retrieve rollback audit event history
- `POST /api/v1/rollout/start/{feature_name}` — Start gradual rollout at 10%
- `POST /api/v1/rollout/advance/{feature_name}` — Advance rollout stage (10% → 25% → 50% → 75% → 100%)
- `GET /api/v1/rollout/status/{feature_name}` — Get current rollout status and stage history

### 5. Shadow Mode API
- `POST /api/v1/shadow/enable/{feature_name}` — Enable background shadow mode
- `POST /api/v1/shadow/disable/{feature_name}` — Disable background shadow mode
- `GET /api/v1/shadow/status/{feature_name}` — Get shadow accuracy and latency comparison metrics
- `GET /api/v1/shadow/history/{feature_name}` — List shadow evaluation logs

### 6. Dashboard
- `GET /dashboard` — Render React + Recharts interactive dashboard UI

---

## 🎬 End-to-End Demo Walkthrough

1. **Access Dashboard**: Open `http://localhost:8000/dashboard` in your browser.
2. **Test Categorization**: Use the *Test AI Categorizer* interactive box to submit expenses. Notice how traffic splits consistently between `categorizer_v1` and `categorizer_v2`.
3. **Enable Shadow Mode**: Click **Enable Shadow Mode**. Subsequent categorizations will run `categorizer_v2` in the background without affecting production responses.
4. **Trigger Quality Degradation**: In the interactive controls, record low quality scores for `categorizer_v2`. The Monitoring Status will instantly switch to **THRESHOLD_VIOLATED**.
5. **Execute Automatic Rollback**: Click **Trigger Rollback Check** (or confirm in modal). Notice how `rollout_percentage` drops to `0.0%`, returning 100% of production traffic safely to `categorizer_v1`.
6. **Advance Gradual Rollout**: Log high quality scores for `categorizer_v2` to restore health, then click **Start Rollout** and **Advance Stage** to step rollout up incrementally to 100%.

---

## 🧪 Testing & Quality Assurance

The system includes 46 unit, integration, and end-to-end tests covering all 14 modules:

```bash
python -m pytest -v
```

Key test files:
- `test_health.py`: Root & health endpoint sanity checks.
- `test_feature_flags.py`: Feature flag CRUD & percentage splits.
- `test_user_assignment.py`: Consistent MD5 hashing assignment distribution.
- `test_database.py`: SQLAlchemy ORM & SQLite fallback repository.
- `test_api.py`: FastAPI REST API endpoints.
- `test_sdk.py`: Python SDK context manager & error handling.
- `test_ai_categorizer.py`: Version A vs Version B AI Categorizer routing.
- `test_quality.py`: Quality score formula & summary stats.
- `test_monitoring.py`: Monitoring logs & threshold violation alerts.
- `test_rollback.py`: Safety circuit-breaker automatic rollback execution.
- `test_rollout.py`: Quality-gated gradual rollout controller.
- `test_dashboard.py`: Dashboard endpoint template rendering.
- `test_shadow.py`: Shadow mode zero-impact background evaluation.
- `test_demo_integration.py`: Complete system lifecycle end-to-end integration test.
