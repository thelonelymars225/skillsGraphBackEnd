from sqlalchemy import select
from app.entities.projects import Projects
from app.database import SessionLocal


def create_project(name: str, description: str) -> Projects:
    db = SessionLocal()
    try:
        project = Projects(name=name, description=description)
        db.add(project)
        db.commit()
        db.refresh(project)
        return project
    finally:
        db.close()


def get_project(id: int) -> Projects | None:
    db = SessionLocal()
    try:
        project = db.scalar(select(Projects).where(Projects.id == id))
        return project
    finally:
        db.close()


def get_projects() -> list[Projects]:
    db = SessionLocal()
    try:
        projects = db.scalars(select(Projects)).all()
        return list(projects)
    finally:
        db.close()


def update_project(id: int, name: str | None = None, description: str | None = None) -> Projects | None:
    db = SessionLocal()
    try:
        project = db.scalar(select(Projects).where(Projects.id == id))
        if project is None:
            return None
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        db.commit()
        db.refresh(project)
        return project
    finally:
        db.close()


def delete_project(id: int) -> bool:
    db = SessionLocal()
    try:
        project = db.scalar(select(Projects).where(Projects.id == id))
        if project is None:
            return False
        db.delete(project)
        db.commit()
        return True
    finally:
        db.close()
