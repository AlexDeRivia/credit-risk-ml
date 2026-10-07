FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY manage.py ./
COPY interbank_loans/ ./interbank_loans/
COPY loans/ ./loans/
COPY templates/ ./templates/
COPY static/ ./static/
COPY ml_models/ ./ml_models/
RUN DJANGO_SECRET_KEY=build-time-placeholder-for-static-assets-only-12345678901234567890 \
    DJANGO_ALLOWED_HOSTS=localhost python manage.py collectstatic --noinput
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["/bin/sh", "-c", "exec gunicorn interbank_loans.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-1} --timeout 60"]
