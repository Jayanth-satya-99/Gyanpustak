from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.routers.books import router as books_router

app = FastAPI(
    title="GyanPustak API",
    version="1.0.0",
)

app.include_router(books_router)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "GyanPustak API",
    }


@app.get("/health/database")
def database_health(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))

    return {
        "database": "connected",
        "result": result.scalar(),
    }
