# skillsGraphBackEnd

A project created with FastAPI CLI.

## Quick Start

### Local PostgreSQL + SQLAlchemy setup

1. Install the locked application and development dependencies:

```bash
uv sync --locked
```

2. Start PostgreSQL on localhost:

```bash
docker compose up -d postgres
```

3. Create your env file. The example matches the Compose database and explicitly
allows the Angular development origin at `http://localhost:4200`:

```bash
cp .env.example .env
```

4. Upgrade the database:

```bash
uv run alembic upgrade head
```

5. Start the API:

```bash
uv run fastapi dev
```

6. Verify application and database health:

- http://localhost:8000/api/v1/health
- http://localhost:8000/api/v1/health/db

### Start the development server

```bash
uv run fastapi dev
```

Visit http://localhost:8000

### Run tests

Tests use injected database engines and do not connect to the development database.

```bash
uv run pytest
```

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
