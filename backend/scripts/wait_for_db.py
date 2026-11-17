import sys
import time
from sqlalchemy import text
from app.core.database import engine


def wait_for_db(max_retries: int = 20, delay: int = 2) -> None:
    print("Checking database readiness...", flush=True)
    for i in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print("Database is ready and accepting connections!", flush=True)
                return
        except Exception as e:
            print(f"Database not ready yet (attempt {i}/{max_retries}): {e}", flush=True)
            time.sleep(delay)
    print("Database connection timed out.", flush=True)
    sys.exit(1)


if __name__ == "__main__":
    wait_for_db()
