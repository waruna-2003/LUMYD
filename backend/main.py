from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import datasets
from app.database.session import Base, engine
from app.models import column, column_stats, dataset  # noqa: F401 - registers models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LUMYD API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router, prefix="/api/v1")


@app.get("/")
def health_check():
    return {"status": "LUMYD System Online"}
