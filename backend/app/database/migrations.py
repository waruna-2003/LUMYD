from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


SEMANTIC_COLUMNS = {
    "technical_type": "VARCHAR",
    "business_type": "VARCHAR",
    "business_role": "VARCHAR",
    "unit": "VARCHAR",
    "aggregation": "JSON",
    "is_derived": "BOOLEAN NOT NULL DEFAULT FALSE",
    "is_redundant": "BOOLEAN NOT NULL DEFAULT FALSE",
}


def ensure_semantic_columns(engine: Engine) -> None:
    """Add Phase 4 fields to databases created before the semantic layer."""
    inspector = inspect(engine)
    if "column_metadata" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("column_metadata")}
    with engine.begin() as connection:
        for name, definition in SEMANTIC_COLUMNS.items():
            if name not in existing:
                connection.execute(
                    text(f'ALTER TABLE column_metadata ADD COLUMN "{name}" {definition}')
                )
