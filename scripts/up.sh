#!/bin/bash
NETWORK_NAME="eventito-dev-network"

# Check if .env file exists, if not create it from .env.example
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

if ! docker network ls --format '{{.Name}}' | grep -wq "$NETWORK_NAME"; then
    echo "Creating network '$NETWORK_NAME'..."
    docker network create "$NETWORK_NAME"
fi

docker compose -f docker-compose-dev.yaml up --build -d
