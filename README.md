# skillsGraphBackEnd

A project created with FastAPI CLI.

## Quick Start

### Local PostgreSQL + SQLAlchemy setup

1. Start PostgreSQL on localhost:

```bash
docker compose up -d postgres
```

2. Create your env file:

```bash
cp .env.example .env
```

3. Start the API:

```bash
uv run fastapi dev
```

4. Verify database connection:

Visit http://localhost:8000/health/db

### Start the development server

```bash
uv run fastapi dev
```

Visit http://localhost:8000

### Deploy to FastAPI Cloud

> FastAPI Cloud is currently in private beta. Join the waitlist at https://fastapicloud.com

```bash
uv run fastapi deploy
```

## Project Structure

- `main.py` - Your FastAPI application
- `pyproject.toml` - Project dependencies

## Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [FastAPI Cloud](https://fastapicloud.com)
