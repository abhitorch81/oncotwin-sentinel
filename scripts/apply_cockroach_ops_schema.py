import os
from pathlib import Path

from sqlalchemy import create_engine

url = os.environ.get("DATABASE_URL", "")
if not url:
    raise SystemExit("DATABASE_URL is not configured")
sql_path = Path(__file__).with_name("cockroach_ops_v11_4.sql")
statements = [item.strip() for item in sql_path.read_text().split(";") if item.strip()]
engine = create_engine(url, pool_pre_ping=True)
with engine.begin() as connection:
    for index, statement in enumerate(statements, 1):
        connection.exec_driver_sql(statement)
        print(f"[{index:02d}/{len(statements):02d}] applied")
engine.dispose()
print("CockroachDB Operations Agent receipt schema is ready.")
