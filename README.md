# AI-Powered Kirana Store Cash Flow Underwriting System

Production-oriented local-first stack for remote kirana underwriting using image, geo, fraud, and calibrated range estimation signals.

## Stack

- Frontend: React, TypeScript, Vite, Tailwind, Redux Toolkit
- Backend: FastAPI, SQLAlchemy, Alembic, Celery, Redis
- Storage: PostgreSQL, MinIO/S3
- ML: OpenCV, Ultralytics YOLOv8 hooks, LightGBM/XGBoost-compatible inference scaffold

## Local setup

1. Copy `.env.example` to `.env`.
2. Start the stack:
   `docker compose up --build`
3. Run migrations:
   `docker compose exec backend alembic upgrade head`
4. Open the apps:
   - Frontend: `http://localhost:5173`
   - API docs: `http://localhost:8000/docs`
   - MinIO: `http://localhost:9001`

## Repo layout

- `backend/`: FastAPI API, workers, models, services, ML scaffolding
- `frontend/`: Merchant and underwriter React app
- `infra/`: deployment and infra placeholders

## Notes

- External geo and explanation providers degrade to deterministic local fallbacks when keys are absent.
- Raw images are designed for short-lived object storage; the cleanup worker enforces retention windows.
- ML inference is wired to a heuristic + model-loader path so the product is runnable before trained artifacts exist.
