#!/bin/bash
BACKEND_RUNNING=$(docker compose -f docker-compose-dev.yaml ps backend | grep -c "backend" || true)

if [ "$BACKEND_RUNNING" -eq 0 ]; then
    echo "Backend container is not running. Starting services..."
    bash ./scripts/up.sh
fi

echo "Running tests..."
docker compose -f docker-compose-dev.yaml exec backend bash -c "pytest --exitfirst; echo 'You can run the tests with pytest --exitfirst'; exec bash"
