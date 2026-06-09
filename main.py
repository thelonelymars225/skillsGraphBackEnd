from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine

app = FastAPI()

@app.get("/")
def main():
    return {"message": "Hello World"}


@app.get("/health/db")
def db_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"database": "ok"}
    except SQLAlchemyError as exc:
        return {"database": "error", "detail": str(exc)}
