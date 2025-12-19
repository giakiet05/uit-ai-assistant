# Development stage - with watchdog for auto-reload
FROM python:3.13-slim AS development

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Install watchdog for live reload
RUN pip install --no-cache-dir watchdog[watchmedo]

# Copy project files (including README.md required by pyproject.toml)
COPY pyproject.toml uv.lock README.md ./

# Install Python dependencies
RUN uv sync --frozen

# Copy source code (will be overridden by volume in dev mode)
COPY . .

# Expose the gRPC port
EXPOSE 50051

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Use watchmedo for auto-restart on file changes
CMD ["watchmedo", "auto-restart", "--directory=./", "--pattern=*.py", "--recursive", "--", "uv", "run", "python", "main.py"]

# Production stage - optimized
FROM python:3.13-slim AS production

WORKDIR /app

# Install system dependencies and uv in one layer, cleanup immediately
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && pip install --no-cache-dir uv \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml uv.lock README.md ./

# Install dependencies and cleanup cache
RUN uv sync --frozen --no-cache

# Copy source code
COPY . .

# Expose the gRPC port
EXPOSE 50051

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "main.py"]