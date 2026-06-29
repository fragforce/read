FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.7.12@sha256:f68150822129ccecd95525e0ee1582f6f9421fa2c04c5afa3efa9c92232a819e /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra dev

COPY . .

CMD ["uv", "run", "--frozen", "pytest"]
