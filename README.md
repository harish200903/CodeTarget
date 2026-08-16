# CodeTarget 🎯

**Company-Specific Coding-Round Preparation Platform**

CodeTarget is a production-grade full-stack web application designed for company-specific interview preparation. Unlike generic competitive programming platforms, CodeTarget personalizes problem recommendations, mock tests, hints, and readiness diagnostics based on real hiring patterns of top technical recruiters (with initial focus on TCS, Cognizant, Infosys, Accenture, Wipro, Deloitte, Capgemini, Zoho, Amazon, and Microsoft).

---

## 🏗️ Architecture & Technology Stack

- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, Monaco Editor (`@monaco-editor/react`), TanStack Query v5.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), AsyncPG, Alembic migrations.
- **Database**: PostgreSQL 16 (Fully normalized relational schema).
- **Caching & Task Queue**: Redis 7.
- **Code Execution Subsystem**: Isolated Judge0 integration behind internal `ExecutionService` backend abstraction.
- **AI Subsystem**: Provider-independent `AIService` abstraction with Google Gemini 2.5 Flash initial provider (`GeminiAIService`).

---

## ⚡ Supported Programming Languages (v1)

- **Python 3**
- **Java**
- **C++**

---

## 🤖 AI Service Infrastructure Architecture (Phase 4A)

CodeTarget uses a provider-independent AI architecture:

```text
Frontend (Next.js)
       ↓
FastAPI Backend (Future Purpose-Specific APIs: /api/v1/ai/*)
       ↓
AIService (Abstract Base Class Interface)
       ↓
GeminiAIService (Google Gemini 2.5 Flash Concrete Provider)
       ↓
Google Gemini API (Official google-genai SDK)
```

### Key AI Features & Design Principles:
1. **Provider Isolation**: Future AI features depend strictly on `AIService`, allowing seamless provider migration without changing application code.
2. **Environment Configuration**: Controlled via `GEMINI_API_KEY`, `GEMINI_MODEL` (default: `gemini-2.5-flash`), `AI_ENABLED` (default: `false`), `AI_REQUEST_TIMEOUT_SECONDS` (15s), `AI_MAX_INPUT_CHARS` (8000), `AI_RATE_LIMIT_PER_MINUTE` (10).
3. **Structured Outputs**: All responses validated using Pydantic schemas (`AIHintResponse`, `AICodeReviewResponse`, `AIErrorExplanationResponse`, `AIRecommendationResponse`).
4. **Prompt Security**: Strict prompt delimiters (`<USER_CODE>`, `<PROBLEM_SPEC>`, `<ERROR_OUTPUT>`) defend against prompt injection attacks. User input cannot override system instructions.
5. **Fail-Safe Operation**: If AI is disabled or Gemini API is unreachable, the application degrades gracefully. Primary problem solving, code execution, and Judge0 function without AI.
6. **Rate Limiting & Caching**: Redis sliding window limits requests to 10/min/user. SHA256 caching caches deterministic requests.
7. **Offline Testing**: Pytest test suite runs 100% offline using mocked provider interfaces (no live Gemini API key required).

---

## 📁 Repository Structure

```
.
├── docker-compose.yml          # Container orchestration (Postgres, Redis, FastAPI, Next.js)
├── .env.example                # Environment variables template
├── README.md                   # Project documentation
├── backend/                    # FastAPI backend service
│   ├── alembic/                # Database migrations
│   ├── app/
│   │   ├── api/                # API router & endpoints
│   │   ├── core/               # Configuration, Database & Redis managers
│   │   ├── models/             # Normalized SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic data & AI response schemas
│   │   └── services/           # ExecutionService & AIService infrastructure
│   └── tests/                  # Pytest test suite (100% pass rate)
└── frontend/                   # Next.js 14 frontend application
    ├── src/
    │   ├── app/                # Next.js App Router pages
    │   ├── components/         # React UI components
    │   └── lib/                # API client & utility helpers
    └── public/                 # Static assets
```

---

## 🚀 Local Setup Instructions

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Docker & Docker Compose (Optional for local container running)

### 2. Local Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- Interactive API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Endpoint: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### 3. Local Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Web Application: [http://localhost:3000](http://localhost:3000)

---

## 🧪 Testing

- **Backend Pytest**:
  ```bash
  cd backend
  pytest
  ```

---

## 🛡️ Data Source Verification Labels

Problem-company associations track verified intelligence sources:
- `OFFICIAL`: Sourced directly from official recruiter sample tests/assessments.
- `VERIFIED`: Sourced from confirmed recent candidate interview experiences.
- `CURATED`: Expertly compiled by technical interview coaches.
- `COMMUNITY_REPORTED`: Submitted and crowd-verified by recent applicants.
- `PATTERN_BASED`: Derived from established recruiter topic distributions.
