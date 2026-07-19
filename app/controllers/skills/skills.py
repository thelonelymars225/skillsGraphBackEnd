from app.services.skills.skills import (
    create_skill,
    delete_skill,
    get_skill,
    get_skills,
    update_skill,
)


def create_skill_controller(name: str, category: str, status: str, hours: int):
    skill = create_skill(name, category, status, hours)
    return skill


def get_skill_controller(id: int):
    skill = get_skill(id)
    return skill


def get_skills_controller():
    skills = get_skills()
    return skills


def update_skill_controller(
    id: int,
    name: str | None = None,
    category: str | None = None,
    status: str | None = None,
    hours: int | None = None,
):
    skill = update_skill(id, name, category, status, hours)
    return skill


def delete_skill_controller(id: int) -> bool:
    return delete_skill(id)