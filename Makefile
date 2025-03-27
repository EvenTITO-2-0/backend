DOCKER_COMPOSE_DEV = docker compose -f docker-compose-dev.yaml

# Build and start the development environment
.PHONY: up
up:
	./scripts/up.sh

# Stop and remove containers
.PHONY: down
down:
	./scripts/down.sh

# Clear PostgreSQL data
.PHONY: clear
clear:
	./scripts/clear.sh

# Run tests inside the container
.PHONY: test
test:
	./scripts/test.sh

# View logs of all containers
.PHONY: logs
logs:
	$(DOCKER_COMPOSE_DEV) logs -f

# Restart all containers
.PHONY: restart
restart:
	$(DOCKER_COMPOSE_DEV) restart

# Enter backend container shell
.PHONY: shell
shell:
	$(DOCKER_COMPOSE_DEV) exec backend bash

# Help command to list all available commands
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  up              - Build and start the development environment"
	@echo "  down            - Stop and remove containers"
	@echo "  clear           - Clear PostgreSQL data"
	@echo "  test            - Run tests inside the container"
	@echo "  logs            - View logs of all containers"
	@echo "  restart         - Restart all containers"
	@echo "  shell           - Enter backend container shell"
	@echo "  help            - Show this help message" 