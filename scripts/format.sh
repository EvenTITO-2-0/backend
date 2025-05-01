#!/bin/bash

# Check if backend container is running
if ! docker compose -f docker-compose-dev.yaml ps --status running | grep -q backend; then
    echo "Backend container is not running. Starting services..."
    ./scripts/up.sh
fi

# Run formatters
docker compose -f docker-compose-dev.yaml exec backend bash -c "ruff check --fix . && ruff format ."
