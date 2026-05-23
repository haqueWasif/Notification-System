#!/bin/sh

python manage.py migrate
python manage.py collectstatic --noinput

celery -A config.celery worker -l info &

gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}