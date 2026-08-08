# 🚀 Blinkly - Setup & Development Guide

Comprehensive instructions for setting up, running, testing, and containerizing the **Blinkly** URL shortener project on your local machine.

---

## 📋 Prerequisites

Ensure you have the following installed on your system:

- **Python**: `>= 3.12`
- **uv**: Fast Python package installer ([Install uv](https://docs.astral.sh/uv/getting-started/installation/))
- **Docker & Docker Compose**: For containerized database, cache, and app execution ([Get Docker](https://docs.docker.com/get-docker/))
- **Git**: For version control

---

## 🛠️ Method 1: Local Development Setup (Recommended for Active Development)

This method runs Django directly on your host machine while using Docker for PostgreSQL and Redis services.

### 1. Clone the Repository
```bash
git clone <repository-url>
cd blinkly
```

### 2. Configure Environment Variables
Copy the example environment configuration file to create `.env`:
```bash
cp .env.example .env
```

Ensure your `.env` is configured for local host connectivity to PostgreSQL (`5433`) and Redis (`6380`):
```env
# DJANGO
DJANGO_DEBUG=True
SITE_URL=http://127.0.0.1:8001
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8001,http://localhost:8001
SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=config.settings.local

# POSTGRESQL
DB_NAME=blinkly
DB_USER=blinkly
DB_PASSWORD=admin
DB_HOST=localhost
DB_PORT=5433

# REDIS
REDIS_URL=redis://127.0.0.1:6380/1

# CELERY
CELERY_BROKER_URL=redis://127.0.0.1:6380/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6380/2
```

### 3. Install Python Dependencies
Use `uv` to install all project and development dependencies into a virtual environment (`.venv`):
```bash
uv sync --dev
```

### 4. Start Database & Redis Services
Launch PostgreSQL and Redis containers using Docker Compose:
```bash
docker compose -f docker/docker-compose.yml up -d db redis
```

### 5. Activate Virtual Environment
```bash
source .venv/bin/activate
```

### 6. Apply Database Migrations
```bash
python manage.py migrate
```

### 7. Run the Django Development Server
```bash
python manage.py runserver 8001
```
Access the application in your browser at `http://127.0.0.1:8001/`.

### 8. Run Celery Worker (In a Separate Terminal Tab)
Open a new terminal tab, navigate to the project directory, activate the environment, and start Celery:
```bash
source .venv/bin/activate
celery -A config worker -l info
```

---

## 🐳 Method 2: Full Docker Setup (Complete Containerized Stack)

Run the entire application stack (Web, Celery worker, PostgreSQL, Redis, and Nginx) inside Docker containers.

### 1. Environment Configuration for Docker
When running inside Docker, set the service hostnames to match the Docker container names in `.env`:
```env
# POSTGRESQL (Container Network Hostname)
DB_HOST=db
DB_PORT=5432

# REDIS & CELERY (Container Network Hostname)
REDIS_URL=redis://redis:6379/1
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/2
```

### 2. Launch Development Stack
Build and bring up all containers in development mode:
```bash
docker compose -f docker/docker-compose.yml up --build
```

Access the app at `http://localhost:8000`.

### 3. Launch Production Stack (With Nginx Reverse Proxy)
To test production mode with Gunicorn WSGI server and Nginx reverse proxy:
```bash
docker compose -f docker/docker-compose.production.yml up --build -d
```

Access the production app at `http://localhost:80` (or `http://localhost`).

### 4. Stop Docker Containers
```bash
docker compose -f docker/docker-compose.yml down
# or for production stack:
docker compose -f docker/docker-compose.production.yml down
```

---

## 🧪 Running Tests & Code Quality Tools

### 1. Run Test Suite
Run tests using Pytest:
```bash
# Run all tests
uv run pytest

# Run tests in parallel
uv run pytest -n auto
```

### 2. Test Coverage
Generate code coverage reports:
```bash
uv run coverage run -m pytest
uv run coverage report
```

### 3. Code Linting & Formatting
Run Ruff linter and formatter:
```bash
# Check code for lint errors
uv run ruff check .

# Format code automatically
uv run ruff format .
```

### 4. Setup Pre-commit Hooks
Automatically run quality checks before every commit:
```bash
uv run pre-commit install
```

---

## 📁 Useful Project Commands Summary

| Command | Description |
| :--- | :--- |
| `python manage.py runserver 8001` | Start local Django dev server |
| `celery -A config worker -l info` | Start Celery worker |
| `docker compose -f docker/docker-compose.yml up -d db redis` | Start local Postgres & Redis containers |
| `docker compose -f docker/docker-compose.production.yml up --build -d` | Start full production Docker stack |
| `uv run pytest -n auto` | Run complete test suite in parallel |
| `uv run ruff format .` | Auto-format codebase using Ruff |
