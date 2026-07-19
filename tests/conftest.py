import os


os.environ.setdefault("DATABASE_URL", (
    "postgresql+psycopg://postgres:postgres@localhost:5432/skills_graph_test"
))
os.environ["CORS_ORIGINS"] = '["http://localhost:4200"]'
