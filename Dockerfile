
FROM python:3.12-slim AS builder

WORKDIR /app


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install building dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies in vendor/wheel form
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final production stage image
FROM python:3.12-slim

WORKDIR /app

# Set env configurations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install runtime postgres libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy built wheels from builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy app code
COPY . /app/

# Setup a non-privileged user for security compliance
RUN useradd -m -u 8888 appuser

RUN mkdir -p /home/appuser \
    && chown -R appuser:appuser /home/appuser \
    && chown -R appuser:appuser /app
# Static collection dummy compile
RUN DJANGO_SECRET_KEY=dummy-secret-key-12345 DJANGO_DEBUG=False python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Apply database migrations, seed demo data if empty, then start the Gunicorn server
CMD ["sh", "-c", "python manage.py migrate --noinput && python seed.py && gunicorn multivendor.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
