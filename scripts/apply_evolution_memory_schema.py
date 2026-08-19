"""Apply the OncoTwin V11.2 persistent evolution memory schema."""
from __future__ import annotations
import os
from pathlib import Path
from sqlalchemy import create_engine

url=os.environ.get("DATABASE_URL","")
if not url:
    raise SystemExit("DATABASE_URL is not configured in this terminal.")
sql_path=Path(__file__).with_name("cockroach_evolution_memory_v11_2.sql")
statements=[part.strip() for part in sql_path.read_text(encoding="utf-8").split(";") if part.strip()]
engine=create_engine(url,pool_pre_ping=True)
with engine.begin() as connection:
    for number,statement in enumerate(statements,1):
        # Execute migration SQL verbatim. SQLAlchemy text() treats JSON such as
        # {"clone-id":1.0} as a named bind parameter (":1"), corrupting seeds.
        connection.exec_driver_sql(statement)
        print(f"[{number:02d}/{len(statements):02d}] applied")
engine.dispose()
print("OncoTwin V11.2 persistent evolution frames and path ledger are ready.")
