from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import Engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, get_engine
from app.schemas.dashboard import ActiveSkillStatus, DashboardSummary
from app.schemas.skills import SkillCreate, SkillRead
from app.services.dashboard import get_dashboard_summary
from app.services.skills import (
    ActiveSkillNameConflictError,
    SkillCategoryNotFoundError,
    create_skill,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
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


@app.post(
    "/api/v1/skills",
    response_model=SkillRead,
    status_code=status.HTTP_201_CREATED,
)
def skill_create(
    skill_create: SkillCreate,
    db: Session = Depends(get_db),
) -> SkillRead:
    try:
        return create_skill(db, skill_create)
    except SkillCategoryNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        ) from error
    except ActiveSkillNameConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active skill with this name already exists.",
        ) from error


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
