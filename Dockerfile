# Mini Shop container image (used by ECS)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 1) Install packages first: this layer is cached until requirements.txt changes
COPY requirements.txt .
RUN pip install -r requirements.txt

# 2) Copy the code
COPY . .

# 3) Collect admin/DRF static files into /app/staticfiles (WhiteNoise serves them).
#    Dummy values: settings.py needs these env vars to load, but collectstatic never touches the DB.
RUN DJANGO_SECRET_KEY=build-only POSTGRES_DB=x POSTGRES_USER=x POSTGRES_PASSWORD=x \
    python manage.py collectstatic --noinput

# 4) Don't run as root inside the container
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Settings for gunicorn live in gunicorn.conf.py (workers/threads come from env vars)
CMD ["gunicorn", "config.wsgi", "-c", "gunicorn.conf.py"]
