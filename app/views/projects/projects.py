from app.controllers.projects.projects import (
    create_project_controller,
    delete_project_controller,
    get_project_controller,
    get_projects_controller,
    update_project_controller,
)


def create_project_view(name: str, description: str):
    project = create_project_controller(name, description)
    return project


def get_project_view(id: int):
    project = get_project_controller(id)
    return project


def get_projects_view():
    projects = get_projects_controller()
    return projects


def update_project_view(id: int, name: str | None = None, description: str | None = None):
    project = update_project_controller(id, name, description)
    return project


def delete_project_view(id: int) -> bool:
    return delete_project_controller(id)
