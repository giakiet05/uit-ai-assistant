FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml ./
COPY uv.lock ./

# Install uv for faster dependency management
RUN pip install uv

# Install dependencies
RUN uv sync --frozen

# Copy source code
COPY . .

# Run the knowledge builder service
CMD ["uv", "run", "python", "main.py"]