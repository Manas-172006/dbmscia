import sys
import time
from sqlalchemy import text
from app.core.database import engine


def wait_for_db(max_retries: int = 20, delay: int = 2) -> None:
    db_host = engine.url.host or "unknown"
    db_port = engine.url.port or 3306
    db_user = engine.url.username or "unknown"
    db_name = engine.url.database or "unknown"
    print(f"Connecting to MySQL: {db_user}@{db_host}:{db_port}/{db_name}", flush=True)
    if db_host in ("127.0.0.1", "localhost"):
        print(
            "WARNING: Connecting to localhost/127.0.0.1! "
            "If deployed on Railway, please add DATABASE_URL or MYSQL_URL in your service's Variables tab.",
            flush=True,
        )
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
