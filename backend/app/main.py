import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.api.v1 import admin, auth, categories, contact, items, locations, me
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Found It University Lost-and-Found Portal API - Powered by MySQL 8",
    version="1.0.0",
)

# CORS configuration
origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists and mount static serving
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "demo"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "user_uploads"), exist_ok=True)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/api/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    try:
        res = db.execute(text("SELECT VERSION() AS ver;")).scalar()
        db_status = "healthy"
        db_version = str(res)
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        db_version = "unknown"

    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database": {
            "engine": "MySQL 8 (InnoDB)",
            "status": db_status,
            "version": db_version,
        },
    }


# Include API Routers
app.include_router(auth.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(locations.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(contact.router, prefix="/api")
app.include_router(me.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
