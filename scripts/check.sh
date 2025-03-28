#!/bin/bash

# Run all checks in sequence
make format
make typecheck
make test
