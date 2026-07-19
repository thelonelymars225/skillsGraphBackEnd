from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.views.skills.skills import (
    create_skill_view,
    delete_skill_view,
    get_skill_view,
    get_skills_view,
    update_skill_view,
)
from app.views.projects.projects import (
    create_project_view,
    delete_project_view,
    get_project_view,
    get_projects_view,
    update_project_view,
)
from app.views.wishlist.wishlist import (
    create_wishlist_item_view,
    delete_wishlist_item_view,
    get_wishlist_item_view,
    get_wishlist_view,
    update_wishlist_item_view,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Root ────────────────────────────────────────────────────────────────
@app.get("/")
def main():
    return {"message": "Hello World"}


# ── Skills ──────────────────────────────────────────────────────────────
@app.post("/skills")
def create_skill(name: str, category: str, status: str, hours: int):
    return create_skill_view(name, category, status, hours)


@app.get("/skills")
def get_skills():
    return get_skills_view()


@app.get("/skills/{id}")
def get_skill(id: int):
    skill = get_skill_view(id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@app.put("/skills/{id}")
def update_skill(
    id: int,
    name: str | None = None,
    category: str | None = None,
    status: str | None = None,
    hours: int | None = None,
):
    skill = update_skill_view(id, name, category, status, hours)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@app.delete("/skills/{id}")
def delete_skill(id: int):
    deleted = delete_skill_view(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"message": "Skill deleted"}


# ── Projects ────────────────────────────────────────────────────────────
@app.post("/projects")
def create_project(name: str, description: str):
    return create_project_view(name, description)


@app.get("/projects")
def get_projects():
    return get_projects_view()


@app.get("/projects/{id}")
def get_project(id: int):
    project = get_project_view(id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.put("/projects/{id}")
def update_project(id: int, name: str | None = None, description: str | None = None):
    project = update_project_view(id, name, description)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.delete("/projects/{id}")
def delete_project(id: int):
    deleted = delete_project_view(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted"}


# ── Wishlist ────────────────────────────────────────────────────────────
@app.post("/wishlist")
def create_wishlist_item(name: str, category: str):
    return create_wishlist_item_view(name, category)


@app.get("/wishlist")
def get_wishlist():
    return get_wishlist_view()


@app.get("/wishlist/{id}")
def get_wishlist_item(id: int):
    item = get_wishlist_item_view(id)
    if item is None:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    return item


@app.put("/wishlist/{id}")
def update_wishlist_item(id: int, name: str | None = None, category: str | None = None):
    item = update_wishlist_item_view(id, name, category)
    if item is None:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    return item


@app.delete("/wishlist/{id}")
def delete_wishlist_item(id: int):
    deleted = delete_wishlist_item_view(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    return {"message": "Wishlist item deleted"}
