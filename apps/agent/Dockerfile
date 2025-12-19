FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install uv

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

CMD ["uv", "run", "python", "main.py"]