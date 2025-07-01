# Multi-stage Dockerfile for Reframe Edge API
# Stage 1: Builder
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock ./

# Install uv for faster dependency installation
RUN pip install uv

# Install dependencies
RUN uv sync --no-dev

# Copy application code
COPY app/ ./app/

# Stage 2: Runtime (distroless)
FROM gcr.io/distroless/python3-debian12

# Copy Python site-packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy application from builder
COPY --from=builder /app /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080
ENV ENVIRONMENT=production

# Set working directory
WORKDIR /app

# Expose port
EXPOSE 8080

# Run the application
ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]