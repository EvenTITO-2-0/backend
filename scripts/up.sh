#!/bin/bash
NETWORK_NAME="eventito-dev-network"

if ! docker network ls --format '{{.Name}}' | grep -wq "$NETWORK_NAME"; then
    echo "Creating network '$NETWORK_NAME'..."
    docker network create "$NETWORK_NAME"
fi

docker compose -f docker-compose-dev.yaml up --build -d
