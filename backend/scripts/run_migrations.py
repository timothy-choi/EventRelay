from __future__ import annotations

import os
import subprocess
import sys

from sqlalchemy import create_engine, inspect


CORE_TABLES = {"endpoints", "events", "deliveries", "delivery_attempts"}
SIMULATION_COLUMNS = {
    "simulation_latency_ms",
    "simulation_failure_rate",
    "simulation_timeout_rate",
}


def run_alembic(*args: str) -> None:
    subprocess.run(
        ["alembic", "-c", "/app/backend/alembic.ini", *args],
        check=True,
    )


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    engine = create_engine(database_url)

    with engine.connect() as connection:
      inspector = inspect(connection)
      tables = set(inspector.get_table_names())

      if "alembic_version" in tables:
          run_alembic("upgrade", "head")
          return

      if not CORE_TABLES.intersection(tables):
          run_alembic("upgrade", "head")
          return

      if CORE_TABLES.issubset(tables):
          endpoint_columns = {column["name"] for column in inspector.get_columns("endpoints")}
          if SIMULATION_COLUMNS.issubset(endpoint_columns):
              run_alembic("stamp", "0002_endpoint_sim")
              run_alembic("upgrade", "head")
          else:
              run_alembic("stamp", "0001_core")
              run_alembic("upgrade", "head")
          return

    print(
        "Existing database schema is partially initialized and cannot be safely auto-stamped.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
