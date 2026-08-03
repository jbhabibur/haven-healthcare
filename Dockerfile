# Stage 1: Build stage (Multi-stage build used to keep image size small)
FROM python:3.11-slim as builder

# Python environment setup
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install system dependencies (For PostgreSQL and Node.js)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements.txt first (For efficient layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Final Runtime stage (This is the production-ready image)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app

# Runtime dependencies (Only essential packages)
RUN apt-get update && apt-get install -y libpq-dev curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy installed libraries from the builder stage
COPY --from=builder /install /usr/local

# Copy all project files
COPY . .

# Create a non-root user (Crucial for production security)
RUN useradd -m havenuser && chown -R havenuser /app
USER havenuser

# Expose the application port
EXPOSE 8000

# Command to run the server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]