# AI Feature Flag System

Safely release new AI versions gradually, monitor their quality, and automatically roll back bad versions.

## Demo Focus
AI Expense Categorizer (Version A vs Version B).

## Architecture & Modules
1. **Module 1: Setup & Architecture** (Current)
2. Module 2: Feature Flag
3. Module 3: User Assignment
4. Module 4: Database
5. Module 5: APIs
6. Module 6: SDK
7. Module 7: AI Integration
8. Module 8: Quality Evaluation
9. Module 9: Monitoring
10. Module 10: Rollback Engine
11. Module 11: Gradual Rollout
12. Module 12: Dashboard
13. Module 13: Shadow Mode
14. Module 14: Testing & Demo

## Getting Started

### Prerequisites
- Python 3.10+

### Setup & Run
```bash
# Install dependencies
pip install -r requirements.txt

# Run pytest unit tests
pytest tests/

# Run dev server
python -m app.main
```

### Endpoints
- `GET /` -> `{"message": "AI Feature Flag System backend is running"}`
- `GET /health` -> `{"status": "ok"}`
