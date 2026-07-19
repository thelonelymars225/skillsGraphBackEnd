from app.controllers.skills.skills import (
    create_skill_controller,
    delete_skill_controller,
    get_skill_controller,
    get_skills_controller,
    update_skill_controller,
)


def create_skill_view(name: str, category: str, status: str, hours: int):
    skill = create_skill_controller(name, category, status, hours)
    return skill


def get_skill_view(id: int):
    skill = get_skill_controller(id)
    return skill


def get_skills_view():
    skills = get_skills_controller()
    return skills


def update_skill_view(
    id: int,
    name: str | None = None,
    category: str | None = None,
    status: str | None = None,
    hours: int | None = None,
):
    skill = update_skill_controller(id, name, category, status, hours)
    return skill


def delete_skill_view(id: int) -> bool:
    return delete_skill_controller(id)