# Development

## Prerequisites

- Docker and Docker Compose
- Git

## Quick Start

```bash
# Clone the repository
git clone git@github.com:fragforce/read.git
cd read

# Copy environment config
cp .env.example .env  # edit with your settings

# Start the dev stack
docker compose up -d

# Run tests
docker compose run --rm test

# Access the app
open http://localhost:8000
```

## Docker Services

| Service | Purpose | Default Command |
|---------|---------|-----------------|
| `web` | Development server with hot reload | `manage.py runserver` |
| `test` | Run the test suite | `pytest` |
| `db` | PostgreSQL 18.3 | - |

The `web` and `test` services use the same image (`Dockerfile`) which includes all dev dependencies. Source code is volume-mounted so changes are reflected immediately.

## Running Tests

```bash
# Full test suite
docker compose run --rm test

# Specific test file
docker compose run --rm test uv run --frozen pytest books/tests/test_playback.py

# With verbose output
docker compose run --rm test uv run --frozen pytest -v

# With coverage
docker compose run --rm test uv run --frozen coverage run -m pytest
docker compose run --rm test uv run --frozen coverage report
```

## Linting

```bash
docker compose run --rm test uv run --frozen ruff check .
docker compose run --rm test uv run --frozen ruff format --check .
```

## Django Management Commands

```bash
docker compose run --rm web uv run --frozen python manage.py migrate
docker compose run --rm web uv run --frozen python manage.py createsuperuser
docker compose run --rm web uv run --frozen python manage.py collectstatic
```

## Project Structure

```
books/           Main app - playback, recording, QR codes, processing
registration/    Narrator registration and login
config/          Django project settings and root URL config
templates/       HTML templates
static/          CSS, JS, and static assets
tests/           Project-level tests (healthz, etc.)
```

## Docker Images

| File | Purpose | Built by |
|------|---------|----------|
| `Dockerfile` | Dev/test image with all dependencies | `docker compose build` |
| `Dockerfile.prod` | Production image (no dev deps, non-root user, collectstatic) | CI workflows |

CI workflows (`dev-image.yaml`, `prod-image.yaml`) build and push `Dockerfile.prod` to GHCR. The dev `Dockerfile` is never pushed to a registry.

## CI Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `coverage.yaml` | Push/PR | Lint, test, upload coverage artifact |
| `django-tests.yaml` | After coverage | Report test results as check run |
| `sonar.yaml` | After coverage | SonarCloud static analysis |
| `dev-image.yaml` | Push to `dev` | Build and push dev container image |
| `prod-image.yaml` | Push to `main` or tag | Build and push prod container image |

## Configuration

Environment variables are loaded from `.env` via django-environ. Key settings:

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Django secret key |
| `DATABASE_URL` | PostgreSQL connection string |
| `DEBUG` | Enable debug mode (never in production) |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames |
