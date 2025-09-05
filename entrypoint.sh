#!/bin/sh
set -e

echo "Waiting for MongoDB..."
RETRIES=30
until nc -z mongo 27017 || [ $RETRIES -eq 0 ]; do
echo "Mongo not up yet... ($RETRIES)"
RETRIES=$((RETRIES-1))
sleep 2
done
[ $RETRIES -eq 0 ] && echo "MongoDB did not become available in time." && exit 1

echo "Running migrations..."
python manage.py makemigrations sugr_backend
python manage.py migrate
python manage.py migrate --noinput

echo "Starting Gunicorn..."
exec gunicorn backend.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 90