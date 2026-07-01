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
| `web` | Development server with hot reload | `uv run --frozen python manage.py runserver 0.0.0.0:8000` |
| `test` | Run the test suite | `uv run --frozen pytest` |
| `db` | PostgreSQL 18.3 | - |

The `web` and `test` services use the same image (`Dockerfile`) which includes all dev dependencies. Source code is volume-mounted so changes are reflected immediately.

## Running Tests

```bash
# Full test suite
docker compose run --rm test

# Specific module
docker compose run --rm test uv run pytest books/tests

# Specific test file
docker compose run --rm test uv run pytest books/tests/test_playback.py

# Specific test
docker compose run --rm test uv run pytest books/tests/test_playback.py::PlaybackViewTest::test_narrator_shown_before_password_entry

# With verbose output
docker compose run --rm test uv run pytest -v

# With coverage
docker compose run --rm test uv run coverage run -m pytest
docker compose run --rm test uv run coverage report
```

## Linting

```bash
# Check for lint issues
docker compose run --rm test uv run ruff check .

# Auto-fix lint issues
docker compose run --rm test uv run ruff check --fix .

# Check formatting
docker compose run --rm test uv run ruff format --check .

# Auto-format code
docker compose run --rm test uv run ruff format .
```

## Development Workflow

### Pre-commit Checks

Before committing code, always run:

```bash
# Lint
docker compose run --rm test uv run ruff check --fix .
docker compose run --rm test uv run ruff format .

# Tests
docker compose run --rm test
```

### Pull Request Requirements

- All tests must pass (146+ tests)
- Lint must pass (ruff check and format)
- Coverage should remain at or above 85%
- SonarCloud quality gate must pass

### Adding Dependencies

```bash
# Add a production dependency
docker compose run --rm web uv add <package>

# Add a dev dependency
docker compose run --rm web uv add --dev <package>

# Sync dependencies after pulling
docker compose run --rm web uv sync --frozen
```

### When Tests Are Required

- **Always** for new features
- **Always** for bug fixes
- **Always** when modifying existing behavior
- Tests should cover the happy path and edge cases

## Database Management

### Creating Migrations

```bash
# Generate migration for model changes
docker compose run --rm web uv run python manage.py makemigrations

# Apply migrations
docker compose run --rm web uv run python manage.py migrate

# Show migration status
docker compose run --rm web uv run python manage.py showmigrations
```

### Resetting the Database

```bash
# Stop services
docker compose down

# Remove database volume
docker volume rm read_pgdata

# Restart and migrate
docker compose up -d
docker compose run --rm web uv run python manage.py migrate
docker compose run --rm web uv run python manage.py createsuperuser
```

### Django Shell

```bash
# Interactive Python shell with Django loaded
docker compose run --rm web uv run python manage.py shell

# Example: Create test data
from books.models import Book
Book.objects.create(title="Test Book", slug="test", author="Author")
```

## Admin Setup

### Creating a Superuser

```bash
docker compose run --rm web uv run python manage.py createsuperuser
```

Then access the admin at `http://localhost:8000/admin/`

### Admin Capabilities

- Manage books, narrators, recordings, QR codes
- Retry failed recordings
- Generate narrator passphrases
- Create event codes and invite links
- Download QR code sheets

## Debugging

### Viewing Logs

```bash
# Follow all service logs
docker compose logs -f

# Follow specific service
docker compose logs -f web

# View recent logs
docker compose logs --tail=100 web
```

### Django Debug Toolbar

When `DEBUG=True`, the Debug Toolbar appears on all pages. Shows:
- SQL queries and performance
- Template rendering
- Request/response headers
- Cache usage

### Container Shell Access

```bash
# Web service shell
docker compose exec web bash

# Database shell
docker compose exec db psql -U fragforce -d fragforce_read
```

## Common Development Tasks

### Testing the Recording Workflow

1. Create a superuser (see Admin Setup)
2. Log in at `/admin/`
3. Create a Book with `public_domain=True`
4. Create an InviteLink or EventCode
5. Register as narrator at `/register/invite/<token>` or `/register/event/`
6. Log in at `/login/` with generated passphrase
7. Select book from dashboard and record

### Creating Test Books

```bash
docker compose run --rm web uv run python manage.py shell
```

```python
from books.models import Book

# Public domain book (no copyright checks)
Book.objects.create(
    title="Alice in Wonderland",
    slug="alice",
    author="Lewis Carroll",
    public_domain=True,
    estimated_duration="30 min"
)

# Licensed book (requires physical book)
Book.objects.create(
    title="Modern Book",
    slug="modern",
    author="Current Author",
    public_domain=False,
    publisher="Publisher Inc",
    max_narrators=3,
    estimated_duration="45 min"
)
```

### Creating Invite Links

Via admin at `/admin/registration/invitelink/add/` or shell:

```python
from registration.models import InviteLink
link = InviteLink.objects.create()
print(f"Invite URL: /register/invite/{link.token}/")
```

### Generating QR Codes

QR codes are auto-generated when recordings finish processing. To regenerate:

1. Go to `/admin/books/qrcode/`
2. Select existing codes
3. Delete and let remux recreate them, or manually create new ones

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

Environment variables are loaded from `.env` via django-environ. Copy `env.sample` to `.env` and customize.

### Core Django Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SECRET_KEY` | string | *required* | Django secret key for cryptographic signing |
| `DEBUG` | bool | `False` | Enable debug mode (never in production) |
| `ALLOWED_HOSTS` | list | `[]` | Comma-separated list of allowed hostnames |
| `CSRF_TRUSTED_ORIGINS` | list | `[]` | Comma-separated list of trusted origins for CSRF |

### Database Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | string | *required* | PostgreSQL connection string (e.g. `postgres://user:pass@host:5432/dbname`) |
| `CONN_MAX_AGE` | int | `600` | Database connection max age in seconds (persistent connections) |
| `POSTGRES_DB` | string | `fragforce_read` | Database name (used by postgres container) |
| `POSTGRES_USER` | string | `fragforce` | Database user (used by postgres container) |
| `POSTGRES_PASSWORD` | string | *required* | Database password (used by postgres container) |

### Security Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SECURE_SSL` | bool | `not DEBUG` | Enable SSL/HTTPS security settings (HSTS, secure cookies) |

### Application Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `RECORDING_MAX_DURATION_SECONDS` | int | `3600` | Maximum allowed recording duration (1 hour) |
| `SESSION_COOKIE_AGE` | int | `604800` | Session lifetime in seconds (default 7 days) |

### Rate Limiting Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LOGIN_MAX_ATTEMPTS` | int | `5` | Maximum login attempts before lockout |
| `LOGIN_LOCKOUT_SECONDS` | int | `300` | Passphrase login lockout duration (5 minutes) |
| `EVENT_LOGIN_LOCKOUT_SECONDS` | int | `60` | Event code registration lockout duration (1 minute) |
| `LOGIN_UNLOCK_CODE` | string | `""` | Optional bypass code for event registration lockout (leave empty to disable) |

### Example Development .env

```bash
# Django
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000

# Database
DATABASE_URL=postgres://fragforce:fragforce@db:5432/fragforce_read
POSTGRES_DB=fragforce_read
POSTGRES_USER=fragforce
POSTGRES_PASSWORD=fragforce

# Application (using defaults, customize if needed)
# RECORDING_MAX_DURATION_SECONDS=3600
# SESSION_COOKIE_AGE=604800
# LOGIN_MAX_ATTEMPTS=5
# LOGIN_LOCKOUT_SECONDS=300
```
