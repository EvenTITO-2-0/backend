FROM python:3.11-slim

# Install basic tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    make \
    docker.io \
    docker-compose \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/backend

# Install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir \
    -r requirements.txt \
    -r requirements-dev.txt
