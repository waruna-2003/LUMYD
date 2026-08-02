from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyst, analytics, datasets
from app.database.migrations import ensure_semantic_columns
from app.database.session import Base, engine
from app.models import column, column_stats, dataset, knowledge, query  # noqa: F401

Base.metadata.create_all(bind=engine)
ensure_semantic_columns(engine)

app = FastAPI(title="LUMYD API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(analyst.router, prefix="/api/v1")


@app.get("/")
def health_check():
    return {"status": "LUMYD System Online"}
