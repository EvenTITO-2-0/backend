#! /bin/bash

# This script removes the pgdata directory, the virtual environment, and the .env.
sudo rm -r pgdata
rm -r .venv
rm .env
