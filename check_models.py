from sqlalchemy import select, text
from db import Base, SessionLocal
from models import Course, Enrollment, Student

DB_NAMES = """
SELECT conname FROM pg_constraint
WHERE connamespace = 'public'::regnamespace AND contype IN ('p', 'u', 'f', 'c')
UNION
SELECT indexname FROM pg_indexes WHERE schemaname = 'public'
"""

with SessionLocal() as db:
    for model in (Course, Student, Enrollment):
        count = len(db.scalars(select(model)).all())
        print(f"{model.__tablename__}: {count} rows")

    in_db = {n for n in db.scalars(text(DB_NAMES)) if not n.startswith("alembic")}
    
    in_models = {
        c.name for table in Base.metadata.tables.values() for c in list(table.constraints) + list(table.indexes)
    }

    print("names only in models:", sorted(in_models - in_db) or "none")
    print("names only in database:", sorted(in_db - in_models) or "none")