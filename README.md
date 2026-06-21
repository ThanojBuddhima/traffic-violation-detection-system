# Sri Lankan Helmet Violation Detection Platform

End-to-end AI platform for automated helmet-violation detection from traffic video. Fine-tunes YOLOv11 on helmet and Sri Lankan license plate datasets, with ByteTrack deduplication and PaddleOCR plate recognition.

## Quick start (V1 local demo)

**Python:** Use **3.12** (`python3.12`). On macOS, `python` is often missing; PaddlePaddle does not support 3.14. Install with: `brew install python@3.12`

### Backend

```bash
python3.12 -m venv .venv312
source .venv312/bin/activate
pip install -r requirements-ml.txt
cp .env.example .env
uvicorn api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:5173 — upload a video, watch processing status, review violations.

### Smoke test

With the API running on port 8000:

```bash
pip install -r requirements-dev.txt
python scripts/test_e2e.py
```

### Mock mode (default)

`USE_MOCK_MODELS=true` in `.env` returns fake violations without trained weights. Set `USE_MOCK_MODELS=false` after placing models in `models/`.

## Environment variables

See [`.env.example`](.env.example) for all keys. Critical ones:

| Variable | V1 default | Description |
|----------|------------|-------------|
| `DATABASE_URL` | `sqlite:///./database/violations.db` | SQLAlchemy connection |
| `STORAGE_BACKEND` | `local` | `local` or `s3` (V2) |
| `USE_MOCK_MODELS` | `true` | Skip YOLO/OCR when no weights |
| `USE_CELERY` | `false` | Use Celery worker (V2) |
| `DELETE_RAW_VIDEO_AFTER_PROCESS` | `false` | Set `true` during Phase 4 testing |

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/videos/upload` | Upload video, start processing |
| GET | `/api/videos` | List all videos |
| GET | `/api/videos/{id}/status` | Video processing status |
| GET | `/api/violations` | List violations (filterable) |
| GET | `/api/violations/{id}/image` | Evidence image |
| PATCH | `/api/violations/{id}` | Update plate / reviewed flag |
| DELETE | `/api/violations/{id}` | Remove false positive |
| GET | `/api/health` | System status |

Interactive docs: http://localhost:8000/docs

## Model training

1. Curate dataset: `python training/scripts/curate_helmet_dataset.py --input /path/to/kaggle --output datasets/helmet`
2. Fine-tune on Kaggle: notebooks in `training/kaggle/`
3. Copy weights to `models/helmet_best.pt` and `models/plate_best.pt`
4. Set `USE_MOCK_MODELS=false`

## Architecture

```
Video upload → FastAPI → job_dispatcher → process_video_job()
  → inference/pipeline (YOLO + ByteTrack + PaddleOCR)
  → storage.save_evidence() + SQLAlchemy DB
```

Abstraction layers for hosting migration:
- `api/storage/` — local disk (V1) or S3 (V2)
- `database/` — SQLAlchemy ORM, `create_all()` (V1) or Alembic (V2)
- `api/services/job_dispatcher.py` — BackgroundTasks (V1) or Celery (V2)

## Hosting migration (V2)

1. Copy `.env.example` values for Postgres, Redis, S3
2. Set `USE_CELERY=true`, `STORAGE_BACKEND=s3`
3. `docker compose up` (api + worker + redis + postgres)
4. Init Alembic: `alembic init database/migrations && alembic upgrade head`
5. Deploy frontend static build with `VITE_API_URL=https://api.yourdomain.com`

See `docker-compose.yml`, [`docs/HOSTING.md`](docs/HOSTING.md), and `scripts/migrate_sqlite_to_postgres.py`.

## Hosting readiness checklist

- [x] File I/O behind `api/storage/`
- [x] DB access via SQLAlchemy ORM only
- [x] `process_video_job()` standalone (no FastAPI imports)
- [x] Config via pydantic-settings + `.env`
- [x] Celery task wrapper in `api/tasks/celery_app.py`
- [x] S3 backend in `api/storage/s3.py`

## CV blurb

> Built an end-to-end AI platform for automated helmet-violation detection from traffic video, fine-tuning YOLOv11 on helmet and Sri Lankan license plate datasets, with object tracking (ByteTrack) for violation deduplication and PaddleOCR for plate recognition. Designed FastAPI backend with async video processing and a React dashboard for violation review.

## License

MIT
