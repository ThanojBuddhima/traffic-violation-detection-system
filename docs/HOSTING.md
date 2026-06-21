# V2 Hosting Guide

## Prerequisites

- Docker and Docker Compose
- S3 bucket (or MinIO for self-hosted)
- Trained model weights in `models/`

## Steps

### 1. Configure environment

```env
DATABASE_URL=postgresql://app:password@postgres:5432/violations
STORAGE_BACKEND=s3
S3_BUCKET=helmet-violations
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_REGION=us-east-1
CELERY_BROKER_URL=redis://redis:6379/0
USE_CELERY=true
USE_MOCK_MODELS=false
CORS_ORIGINS=https://your-frontend.example.com
DB_PASSWORD=your-secure-password
```

### 2. Start services

```bash
docker compose up --build
```

### 3. Initialize Alembic (first deploy only)

```bash
pip install alembic
alembic init database/migrations
# Edit alembic.ini: sqlalchemy.url = %(DATABASE_URL)s
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

### 4. Migrate existing SQLite data (optional)

```bash
export SQLITE_URL=sqlite:///./database/violations.db
export POSTGRES_URL=postgresql://app:password@localhost:5432/violations
python scripts/migrate_sqlite_to_postgres.py
aws s3 sync violations/ s3://helmet-violations/violations/
```

### 5. Deploy frontend

```bash
cd frontend
VITE_API_URL=https://api.yourdomain.com npm run build
# Deploy dist/ to Vercel, Netlify, or S3+CloudFront
```

## Verification

- `GET /api/health` shows `use_celery: true`, `storage_backend: s3`
- Upload video → API returns immediately → worker processes in background
- Restart API container → in-progress jobs continue in worker
