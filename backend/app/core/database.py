from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# MySQL connection with PyMySQL
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    echo=False
)

sql_explorer_engine = (
    create_engine(
        settings.SQL_EXPLORER_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=2,
        max_overflow=0,
        echo=False,
    )
    if settings.SQL_EXPLORER_DATABASE_URL
    else None
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
