# Backend Service Scaffold

Minimal FastAPI backend scaffold for the loyalty platform.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

## Endpoints

- `GET /api/v1/health`
- `GET /api/v1/loyalty/accounts/{member_id}`
