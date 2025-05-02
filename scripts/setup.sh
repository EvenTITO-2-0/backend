#!/bin/bash

# Check if make is installed
if ! command -v make &> /dev/null; then
    echo "make is not installed. Attempting to install..."

    # Check if apt-get is available
    if ! command -v apt-get &> /dev/null; then
        echo "This script requires apt-get (Ubuntu/Debian)"
        echo "Please install make manually or use the Dev Container"
        exit 1
    fi

    # Install make
    echo "Installing make..."
    sudo apt-get update
    sudo apt-get install -y make

    # Verify installation
    if ! command -v make &> /dev/null; then
        echo "make installation failed."
        exit 1
    fi
    echo "make installed successfully!"
fi

# Check if Python 3.11 is installed
if ! command -v python3.11 &> /dev/null; then
    echo "Python 3.11 is not installed. Attempting to install..."

    # Check if apt-get is available
    if ! command -v apt-get &> /dev/null; then
        echo "This script requires apt-get (Ubuntu/Debian)"
        echo "Please install Python 3.11 manually or use the Dev Container"
        exit 1
    fi

    # Install Python 3.11
    echo "Installing Python 3.11..."
    sudo apt-get update
    sudo apt-get install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt-get update
    sudo apt-get install -y python3.11 python3.11-venv

    # Verify installation
    if ! command -v python3.11 &> /dev/null; then
        echo "Python 3.11 installation failed."
        exit 1
    fi
    echo "Python 3.11 installed successfully!"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -r requirements-dev.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

# Run database setup
echo "Running database setup..."
docker compose -f docker-compose-dev.yaml up -d postgres && echo "Waiting for postgres to be ready..." && sleep 10
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ python3.11 scripts/database_setup.py

echo "Local setup complete! You can now:"
echo "1. Use 'source .venv/bin/activate' to activate the virtual environment"
echo "2. Use VSCode's Python interpreter from .venv"
echo "3. Run 'make up' to start the Docker services"
