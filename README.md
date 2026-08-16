# CodeTarget — Company-Specific Coding-Round Preparation Engine

CodeTarget is a production-ready, company-focused coding practice platform designed to prepare candidates for online assessments and technical interview rounds at target companies (e.g., TCS, Cognizant, Infosys, Accenture, Wipro, Deloitte, Capgemini, Zoho, Amazon, Microsoft).

---

## 🏗️ System Architecture

```text
                                  Internet
                                     |
                                     v
                               HTTPS / Domain
                                     |
                       +-------------+-------------+
                       |                           |
                       v                           v
              Next.js Frontend              FastAPI Backend
              (TypeScript + Tailwind)       (Pydantic + SQLAlchemy)
                                                   |
                             +---------------------+---------------------+
                             |                     |                     |
                             v                     v                     v
                        PostgreSQL               Redis             External APIs
                    (Authoritative DB)     (Cache/Rate Limit)      /           \
                                                                 /             \
                                                              Judge0          Gemini
```

- **Frontend**: Next.js 14 (App Router), TypeScript, TailwindCSS, Monaco Code Editor.
- **Backend**: FastAPI, Pydantic V2, SQLAlchemy 2.0 (AsyncIO), Alembic migrations.
- **Database**: PostgreSQL 16 (Authoritative persistence for users, catalog, progress, sessions, XP ledger).
- **Cache & Rate Limiter**: Redis 7 (Caching for recommendations, preparation scores, AI hints; rate limiting for submissions and Gemini API).
- **Code Execution Engine**: Judge0 API abstraction (supports Python, Java, C++ multi-language evaluation).
- **AI Infrastructure**: Google Gemini 2.5 Flash (`AIService` abstraction with prompt injection protection, caching, rate limiting, and structured response parsing).

---

## 🚀 Quick Start — Local Development

### Prerequisites
- Docker & Docker Compose (v2.0+)
- Python 3.11+
- Node.js 20+

### Option 1: Docker Compose (Recommended for Dev)
```bash
# 1. Clone repository
git clone https://github.com/harish200903/CodeTarget.git
cd CodeTarget

# 2. Copy environment file
cp .env.example .env

# 3. Start full stack (PostgreSQL, Redis, Backend, Frontend)
docker compose up --build -d

# 4. Run Alembic database migrations
docker compose exec backend alembic upgrade head

# 5. Access applications
# Frontend: http://localhost:3000
# Backend API & Docs: http://localhost:8000/docs
```

### Option 2: Manual Local Setup
```bash
# Backend Setup
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend Setup (in new terminal)
cd frontend
npm install
npm run dev
```

---

## 🔐 Production Deployment & Configuration Guide

### 1. Recommended Production Infrastructure Target
- **Frontend**: Vercel / AWS Amplify / Cloudflare Pages / Railway (`node server.js` standalone build).
- **Backend**: AWS ECS / Render / Railway / DigitalOcean App Platform (FastAPI with Uvicorn/Gunicorn ASGI server).
- **PostgreSQL**: Managed PostgreSQL (AWS RDS / Supabase / Neon / Render Postgres) with SSL enabled.
- **Redis**: Managed Redis (Upstash / AWS ElastiCache / Redis Cloud) with TLS and authentication password.
- **Judge0**: Self-hosted Judge0 instance or RapidAPI / Judge0 Cloud.
- **Gemini**: Google Cloud Vertex AI / Google AI Studio API Key.

### 2. Production Environment Variables Checklist

| Variable Name | Purpose | Production Requirement |
|---|---|---|
| `ENVIRONMENT` | Operating Mode | Set to `production` |
| `SECRET_KEY` | JWT Secret Key | High-entropy 64+ char random string |
| `DATABASE_URL` | PostgreSQL Async Connection | `postgresql+asyncpg://user:pass@host:5432/dbname?ssl=require` |
| `REDIS_URL` | Redis Cache Connection | `rediss://:password@host:6379/0` |
| `BACKEND_CORS_ORIGINS` | Allowed Frontend Origins | `["https://app.codetarget.com"]` (NO wildcard `*`) |
| `NEXT_PUBLIC_API_URL` | Frontend API Target | `https://api.codetarget.com` |
| `GEMINI_API_KEY` | Google Gemini API Key | Backend-only (Never expose in frontend) |
| `JUDGE0_URL` | Judge0 Endpoint | `https://judge0.yourdomain.com` |
| `JUDGE0_API_KEY` | Judge0 Authorization | Backend-only |
| `AI_ENABLED` | Toggle Gemini AI Features | `true` |

### 3. Step-by-Step Production Deployment Order
1. **Provision Databases**: Provision managed PostgreSQL 16 and Redis 7 instances.
2. **Execute Schema Migrations**:
   ```bash
   cd backend
   alembic upgrade head
   ```
3. **Deploy FastAPI Backend**: Launch backend container/service with production environment variables and `ENVIRONMENT=production`.
4. **Verify Health Endpoint**: Query `https://api.codetarget.com/api/v1/health` (must return `status: "ok"` with healthy database and Redis statuses).
5. **Deploy Next.js Frontend**: Deploy Next.js production build (`npm run build`).
6. **Configure SSL & Custom Domain**: Enable HTTPS on custom domain routes and configure CORS origins.

---

## 🛡️ Database Migrations, Backups & Rollback Plan

### Safe Migration Procedure
- Always run database migrations using `alembic upgrade head` before starting new backend application versions.
- All migrations (`001` through `010`) are additive and idempotent to prevent data loss.

### Production Database Backup Strategy
- **Automated Daily Backups**: Enable managed PostgreSQL provider's automated daily snapshot backups with a 30-day retention window.
- **Point-In-Time Recovery (PITR)**: Enable write-ahead logging (WAL) archiving for 7-day point-in-time recovery.
- **Manual Snapshot**: Create a manual DB snapshot prior to running any major schema migration.

### Emergency Rollback Strategy
1. **Application Rollback**: Revert backend and frontend deployments to the previous stable release commit hash.
2. **Database Rollback**: If a schema migration must be reverted, execute `alembic downgrade -1` (only if migration is forward-compatible) or restore PostgreSQL to pre-migration snapshot.

---

## 🔑 Secure Administrator Account Bootstrapping

To create the initial administrator account securely without hardcoding default credentials:

```bash
# Run interactive CLI script on backend server instance
cd backend
python -c "
import asyncio, uuid
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole, SkillLevel

async def bootstrap():
    async with AsyncSessionLocal() as db:
        admin = User(
            id=uuid.uuid4(),
            email='admin@codetarget.com',
            password_hash=get_password_hash('CHANGE_IMMEDIATELY_UPON_FIRST_LOGIN'),
            full_name='System Administrator',
            role=UserRole.ADMIN,
            skill_level=SkillLevel.ADVANCED,
            onboarding_completed=True
        )
        db.add(admin)
        await db.commit()
        print('Admin account created successfully.')

asyncio.run(bootstrap())
"
```

---

## 🧪 Testing & CI/CD Pipeline

CodeTarget uses GitHub Actions for continuous integration testing on every push and pull request.

```bash
# Run full Pytest backend suite (68+ tests)
cd backend
python -m pytest

# Run Next.js frontend production build & typecheck
cd frontend
npm run build
```

---

## 📜 License & Author

Copyright © 2026 CodeTarget Team. All rights reserved.
