# Multi-stage build for Django ECommerce Application
# Stage 1: Build stage - Install dependencies and collect static files
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
# These are needed for building Python packages and running the application
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage 2: Production stage - Copy only necessary files
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.local/bin:$PATH"

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Set work directory
WORKDIR /app

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project files
COPY --chown=appuser:appuser . .

# Create directories for media and static files
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Collect static files (will be done in entrypoint for production)
# This is done at runtime to ensure environment variables are set

# Expose port 8000 (Gunicorn will run on this port)
EXPOSE 8000

# Default command (can be overridden in docker-compose.yml)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "ECommerce.wsgi:application"]

