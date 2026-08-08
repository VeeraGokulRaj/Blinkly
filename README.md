# ⚡ Blinkly

A high-performance, asynchronous URL shortener application built with **Django 6.0**, **Python 3.12**, **PostgreSQL 16**, **Redis 7**, **Celery**, and **Nginx**.

---

## ✨ Features

- **Base62 URL Shortening**: Fast, deterministic short code generation using Base62 encoding.
- **Asynchronous Click Analytics**: Offloaded user-agent, referer, and device tracking using Celery tasks.
- **Redis Caching**: 24-hour cached URL lookups for ultra-low latency redirection.
- **Containerized Architecture**: Production-ready Docker Compose stack featuring Gunicorn, Celery, PostgreSQL, Redis, and Nginx.
- **Automated Testing & CI/CD**: Comprehensive Pytest suite and GitHub Actions workflow.

---

## 🚀 Getting Started

For detailed setup instructions covering local development, Docker execution, test runner commands, and code formatting tools, see the [Setup & Development Guide](SETUP.md).

### Quick Start (Local Development)

```bash
# 1. Environment configuration
cp .env.example .env

# 2. Install dependencies
uv sync --dev

# 3. Start Database & Redis containers
docker compose -f docker/docker-compose.yml up -d db redis

# 4. Apply migrations & run server
source .venv/bin/activate
python manage.py migrate
python manage.py runserver 8001
```

### Quick Start (Full Docker Stack)

```bash
docker compose -f docker/docker-compose.production.yml up --build -d
```

### Running Tests

```bash
uv run pytest -n auto
```

For full documentation, configuration options, and troubleshooting, read [`SETUP.md`](SETUP.md).
