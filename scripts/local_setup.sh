#!/bin/bash

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

echo "Local setup complete! You can now:"
echo "1. Use 'source .venv/bin/activate' to activate the virtual environment"
echo "2. Use VSCode's Python interpreter from .venv"
echo "3. Run 'make up' to start the Docker services"
