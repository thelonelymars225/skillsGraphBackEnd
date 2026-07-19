from typing import Annotated

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import Engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, get_engine
from app.schemas.dashboard import ActiveSkillStatus, DashboardSummary
from app.services.dashboard import get_dashboard_summary

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def main():
    return {"message": "Hello World"}


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


@app.get("/api/v1/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    status: Annotated[ActiveSkillStatus | None, Query()] = None,
    category_id: Annotated[int | None, Query(gt=0)] = None,
    db: Session = Depends(get_db),
) -> DashboardSummary:
    return get_dashboard_summary(db, status=status, category_id=category_id)


@app.get("/api/v1/health/db")
def db_health(database_engine: Engine = Depends(get_engine)):
    try:
        with database_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"database": "ok"}
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={"database": "unavailable"},
        )
