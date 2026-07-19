from app.services.projects.projects import (
    create_project,
    delete_project,
    get_project,
    get_projects,
    update_project,
)


def create_project_controller(name: str, description: str):
    project = create_project(name, description)
    return project


def get_project_controller(id: int):
    project = get_project(id)
    return project


def get_projects_controller():
    projects = get_projects()
    return projects


def update_project_controller(id: int, name: str | None = None, description: str | None = None):
    project = update_project(id, name, description)
    return project


def delete_project_controller(id: int) -> bool:
    return delete_project(id)
