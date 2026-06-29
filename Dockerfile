FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_NO_CACHE=1

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.7.12@sha256:f68150822129ccecd95525e0ee1582f6f9421fa2c04c5afa3efa9c92232a819e /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

RUN SECRET_KEY=build DATABASE_URL=sqlite:///dev/null uv run --frozen python manage.py collectstatic --noinput

RUN mkdir -p /app/media/recordings /app/media/processing /app/media/finalized \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["uv", "run", "--frozen", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
