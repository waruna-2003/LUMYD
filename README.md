# LUMYD

**LUMYD (Let Us Mine Your Data)** is a full-stack business-intelligence platform that transforms uploaded CSV and Excel datasets into structured metadata, statistical profiles, semantic business knowledge, persisted evidence, and traceable answers to natural-language questions.

---

## Project Status

LUMYD is under active development. The ingestion pipeline, semantic discovery, statistical knowledge-building, evidence-backed analyst engine, and the **Gemini-powered active learning bootstrap** are operational.

### Implemented Features

- **Dataset Ingestion**: CSV, XLS, and XLSX uploads with size (50 MB) and type validation.
- **UUID-based File Storage & PostgreSQL Records**: Safe multi-user uploads with background tracking.
- **Technical & Semantic Discovery**: Automated inference of business roles (`MEASURE`, `RATE`, `DIMENSION`, `ENTITY`, `IDENTIFIER`, `TIME_DIMENSION`), units, supported aggregations, and derived/redundant columns.
- **Deep Statistical Column Profiles**: Mean, median, range, standard deviation, IQR-based outlier detection, and 10-bin distribution histograms.
- **Pairwise Evidence Discovery**: Statistical links via **One-way ANOVA** (categorical $\times$ numeric) and **Pearson Correlation** (numeric $\times$ numeric).
- **Persisted Combination Store**: Fast dimension-level pre-aggregated metrics (sum, mean, count) with SHA-256 combination hashing.
- **Traceable Business Question Answering**: Natural-language query parsing tied directly to persisted `fact_id` and `relationship_id` evidence packages.
- **Active Learning & Synthetic Data Bootstrap (New)**:
  - Synthetic Query Generation powered by `gemini-3.6-flash` supporting English, business colloquialisms, and code-mixed **Singlish** (*"sales adu une ai mcn"*).
  - Ground-truth intent and slot extraction across 5 core analytical tasks (`root_cause`, `ranking`, `comparison`, `trend`, `distribution`).
  - **Gemini Free-Tier Quota Guard**: Client-side rate-limiting ($\ge 4.1\text{s}$ interval $\le 15$ RPM), daily safety ceiling (1,000 requests/day), persistent quota tracking, query caching, and exponential backoff.
- **Modern Responsive Frontend**: React 19, TypeScript, Material UI editorial warm design system, dataset library, schema inspector, and question interface.

---

## Processing & Intelligence Pipeline

```text
Upload CSV / Excel Dataset
            ↓
Store File & Initialize PostgreSQL Record
            ↓
Technical & Semantic Discovery (Roles, Types, Units)
            ↓
Statistical Column Profiling (Distributions & Outliers)
            ↓
Pairwise Evidence Mining (ANOVA & Pearson Correlation)
            ↓
Persisted Combination Store Indexing
            ↓
Natural Language Understanding (Local Router + Gemini Active Learning)
            ↓
Evidence Retrieval & Traceable Answer Generation
```

---

## Technology Stack

### Frontend
- **React 19**
- **TypeScript**
- **Vite**
- **Material UI (MUI)**
- **Axios**

### Backend
- **FastAPI**
- **SQLAlchemy**
- **PostgreSQL**
- **Pydantic v2**
- **Google GenAI SDK (`google-genai`)** (`gemini-3.6-flash`)
- **Pandas, NumPy & SciPy**
- **Uvicorn**

---

## Architecture: Active Learning & Dual-Stage Router

To handle diverse user questions across formal English, informal slang, and code-mixed **Singlish**, LUMYD is adopting a dual-stage neural routing framework:

```text
               User Query (English / Singlish)
                             │
                             ▼
            ┌─────────────────────────────────┐
            │   Semantic Router & OOD Check   │
            │   (paraphrase-multilingual)     │
            └────────────────┬────────────────┘
                             │
              Confidence Score vs. Threshold θ
            ┌────────────────┴────────────────┐
            │                                 │
      Score ≥ θ (Known)                 Score < θ (Novel/Ambiguous)
            │                                 │
            ▼                                 ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│  LUMYD Analytics Pipeline   │   │     Gemini Teacher API      │
│ (ANOVA, Pearson, Combos)    │   │ (Zero-Shot Slot Extraction  │
│                             │   │   + Intent Classification)  │
└─────────────────────────────┘   └──────────────┬──────────────┘
                                                 │
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │    Active Learning Store    │
                                  │ (Update Router Centroids &  │
                                  │  LoRA Fine-Tune Local SLM)  │
                                  └─────────────────────────────┘
```

---

## API Endpoints

### System & Datasets
```text
GET  /
GET  /api/v1/datasets
POST /api/v1/datasets/upload
GET  /api/v1/datasets/{dataset_id}/schema
```

### Analytics & Statistical Knowledge
```text
GET /api/v1/analytics/{dataset_id}/evidence
GET /api/v1/analytics/{dataset_id}/relationships
GET /api/v1/analytics/{dataset_id}/facts
```

### Analyst Engine
```text
POST /api/v1/analyst/{dataset_id}/query
```

**Example Request:**
```json
{
  "query_text": "What are the top regions by sales amount and why?"
}
```

Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

---

## Local Setup

### 1. Environment Configuration

Create `backend/.env` (see `backend/.env.example`):

```env
DATABASE_URL=postgresql://user:password@localhost:5432/lumyd
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Backend Setup

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 3. Generate Synthetic Queries (Active Learning Bootstrap)

To populate the synthetic query training set with quota-guarded Gemini generation:

```powershell
# Live generation with Gemini (respecting Free Tier rate limits):
python backend/scripts/generate_synthetic_queries.py --samples-per-intent 20

# Or offline mock generation (no API calls):
python backend/scripts/generate_synthetic_queries.py --offline-mock --samples-per-intent 50
```

### 4. Frontend Setup

From the repository root:

```powershell
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## Development Checks

```powershell
# Frontend lint & build
cd frontend
npm run lint
npm run build
```

---

## Repository Structure

```text
LUMYD/
├── backend/
│   ├── app/
│   │   ├── api/          # Dataset, analytics, and analyst routes
│   │   ├── core/         # Gemini Quota Guard & rate limiting
│   │   ├── database/     # SQLAlchemy session & compatibility migrations
│   │   ├── models/       # Dataset, metadata, stats, knowledge, query models
│   │   ├── schemas/      # Pydantic request and response schemas
│   │   ├── services/     # Ingestion, profiling, relationship & retrieval engines
│   │   └── utils/        # File validation utilities
│   ├── data/             # Synthetic query datasets & quota trackers
│   ├── scripts/          # Synthetic query generator & utilities
│   ├── uploads/          # Local storage for uploaded files (git-ignored)
│   ├── .env.example      # Environment variables template
│   ├── main.py           # FastAPI entrypoint
│   └── requirements.txt  # Python backend dependencies
└── frontend/
    └── src/
        ├── components/   # FileUpload, SchemaTable, ColumnProfileCard, AnalystPanel
        ├── services/     # Axios API client
        ├── App.tsx       # Main dashboard application
        └── main.tsx      # Theme provider & root entrypoint
```

---

## Security Notes

- **Never commit `.env` files or API keys.**
- Uploaded datasets and runtime trackers (`gemini_quota_tracker.json`) are excluded from Git.
- Free-tier rate limits and safety budgets are strictly enforced by `GeminiQuotaGuard`.

---

## License

All rights reserved.
