# LUMYD

**LUMYD (Let Us Mine Your Data)** is a full-stack business-intelligence platform that transforms uploaded CSV and Excel datasets into structured metadata, statistical profiles, semantic business knowledge, persisted evidence, and traceable answers to natural-language questions.

## Project status

LUMYD is under active development. The ingestion, knowledge-building, and evidence-backed analyst foundations are operational.

### Implemented

- Dataset ingestion for CSV, XLS, and XLSX files
- File-type validation and a 50 MB upload limit
- UUID-based file storage and PostgreSQL dataset records
- Background metadata extraction and processing status tracking
- Row, column, datatype, nullability, and cardinality discovery
- Business-type and business-role inference
- Currency, percentage, and aggregation inference
- Derived and redundant column detection
- Numeric statistics, categorical distributions, and outlier detection
- Persisted column profiles and histogram data
- Pairwise categorical/numeric and numeric/numeric evidence
- Persisted Combination Store with aggregated business facts
- Query-adaptive evidence ranking
- Dataset-aware natural-language query parsing
- Persisted analyst queries with fact and relationship trace IDs
- React interfaces for upload, schema inspection, profiles, and questions

### Current processing pipeline

```text
Upload and validate dataset
        ↓
Store file and dataset record
        ↓
Discover technical schema
        ↓
Infer business semantics
        ↓
Build statistical column profiles
        ↓
Discover pairwise relationships
        ↓
Build the persisted Combination Store
        ↓
Answer questions using ranked, traceable evidence
```

## Technology stack

### Frontend

- React 19
- TypeScript
- Vite
- Material UI
- Axios

### Backend

- FastAPI
- SQLAlchemy
- Pydantic
- Pandas
- NumPy
- SciPy
- Uvicorn

### Database

- PostgreSQL

## Main features

### Dataset ingestion

Uploaded files are assigned UUID filenames and stored in `backend/uploads`. Original filenames, storage paths, processing status, row counts, and column counts are stored in PostgreSQL.

### Metadata and semantic discovery

Every column receives technical and business metadata, including:

- Technical and Python datatype
- Business type: `NUMERIC`, `CATEGORICAL`, `DATETIME`, or `TEXT`
- Business role: `MEASURE`, `RATE`, `DIMENSION`, `ENTITY`, `IDENTIFIER`, or `TIME_DIMENSION`
- Unit and supported aggregations
- Nullability, derived status, and redundancy status

### Column Knowledge Builder

LUMYD calculates and persists:

- Mean, median, minimum, maximum, and standard deviation
- Unique-value and null counts
- IQR-based outlier counts
- Numeric histogram distributions
- Top-value categorical distributions

### Evidence and Combination Store

The evidence layer stores relationships between dimensions and measures, significant numeric correlations, effect strengths, significance values, and supporting details. The Combination Store persists dimension-level sums, means, and counts for fast retrieval.

### Ask LUMYD

Users can select a processed dataset and ask questions such as:

```text
What are the top regions by sales amount and why?
```

The hybrid parser detects the intent, metric, dimensions, filters, and time context. The retrieval engine ranks persisted facts and returns traceable evidence containing query, fact, and relationship IDs.

This is currently an evidence-retrieval interface, not a generative LLM response layer.

## API endpoints

### System and datasets

```text
GET  /
GET  /api/v1/datasets
POST /api/v1/datasets/upload
GET  /api/v1/datasets/{dataset_id}/schema
```

### Analytics and persisted knowledge

```text
GET /api/v1/analytics/{dataset_id}/evidence
GET /api/v1/analytics/{dataset_id}/relationships
GET /api/v1/analytics/{dataset_id}/facts
```

### Analyst

```text
POST /api/v1/analyst/{dataset_id}/query
```

Example request:

```json
{
  "query_text": "What are the top regions by sales amount and why?"
}
```

Interactive API documentation is available at `http://localhost:8000/docs` while the backend is running.

## Local setup

### 1. PostgreSQL

Create a PostgreSQL database and user, then add `backend/.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/lumyd
```

The application creates new tables automatically. A compatibility migration adds semantic fields to databases created by earlier project phases.

### 2. Backend

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend runs at `http://127.0.0.1:8000`.

### 3. Frontend

Create `frontend/.env` if a different API URL is required:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

Then run:

```powershell
cd frontend
npm install
npm run dev
```

The frontend normally runs at `http://localhost:5173`.

## Development checks

```powershell
cd frontend
npm run lint
npm run build
```

## Repository structure

```text
LUMYD/
├── backend/
│   ├── app/
│   │   ├── api/          # Dataset, analytics, and analyst routes
│   │   ├── database/     # SQLAlchemy session and compatibility migration
│   │   ├── models/       # Dataset, metadata, stats, knowledge, and query tables
│   │   ├── schemas/      # API request and response models
│   │   ├── services/     # Ingestion and intelligence pipeline
│   │   └── utils/        # Upload validation
│   ├── uploads/          # Git-ignored uploaded datasets
│   ├── main.py
│   └── requirements.txt
└── frontend/
    └── src/
        ├── components/   # Upload, schema, profile, and analyst interfaces
        ├── services/     # Backend API client
        └── App.tsx
```

## Remaining roadmap

- LLM-generated narrative answers with evidence citations
- Time-aware trend and comparison calculations
- Multi-dimension combination facts
- Dataset deletion and explicit reprocessing controls
- Authentication and user-specific workspaces
- Database migrations managed through Alembic
- Automated backend and frontend tests
- Forecasting and recommendation engines
- Production deployment, monitoring, and CI/CD

## Security notes

- Do not commit `.env` files or database credentials.
- Uploaded datasets are excluded from Git.
- CORS is currently configured for the local Vite development origin.

## License

No license has been specified yet.
