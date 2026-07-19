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
from app.schemas.skills import SkillCreate, SkillRead, SkillUpdate
from app.services.dashboard import get_dashboard_summary
from app.services.skills import (
    ActiveSkillNameConflictError,
    SkillCategoryNotFoundError,
    SkillNotFoundError,
    archive_skill,
    create_skill,
    list_skills,
    restore_skill,
    update_skill,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
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


@app.get("/api/v1/skills", response_model=list[SkillRead])
def skill_list(
    include_archived: bool = False,
    db: Session = Depends(get_db),
) -> list[SkillRead]:
    return list_skills(db, include_archived=include_archived)


def _skill_operation(operation, *args):
    try:
        return operation(*args)
    except SkillNotFoundError as error:
        raise HTTPException(status_code=404, detail="Skill not found.") from error
    except SkillCategoryNotFoundError as error:
        raise HTTPException(status_code=404, detail="Category not found.") from error
    except ActiveSkillNameConflictError as error:
        raise HTTPException(
            status_code=409,
            detail="An active skill with this name already exists.",
        ) from error


@app.put("/api/v1/skills/{skill_id}", response_model=SkillRead)
def skill_update(skill_id: int, update: SkillUpdate, db: Session = Depends(get_db)):
    return _skill_operation(update_skill, db, skill_id, update)


@app.post("/api/v1/skills/{skill_id}/archive", response_model=SkillRead)
def skill_archive(skill_id: int, db: Session = Depends(get_db)):
    return _skill_operation(archive_skill, db, skill_id)


@app.post("/api/v1/skills/{skill_id}/restore", response_model=SkillRead)
def skill_restore(skill_id: int, db: Session = Depends(get_db)):
    return _skill_operation(restore_skill, db, skill_id)


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
