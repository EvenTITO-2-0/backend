[![codecov](https://codecov.io/gh/EvenTITO/backend/graph/badge.svg?token=8HYPP8CZJ6)](https://codecov.io/gh/EvenTITO/backend)

# Users

## Config pre-commit for autolint
```
pip install pre-commit
pre-commit install
```

## Tests
```bash
docker run -it -v $(pwd)/app:/code/app -v $(pwd)/tests:/code/tests eventito:latest bash
```

```bash
pip install pytest
pytest
```


# Migrations

If there are new models, include the model in the file `migrations/env.py`. This is done so that the Base variable includes all the metadata.

0. `pip install alembic`
1. Create a `.env` file containing the DATABASE_URL. It must be async (starts with "postgresql+asyncpg").
2. If the migrations were already applied to the database, run `alembic stamp head`. This will stamp the current state.
3. Modify a model and run  `alembic revision --autogenerate -m "Message specifying the change"`
4. Read the migration file in `migrations/versions`, and if it is okey, run `alembic upgrade head`.


Alembic creates a table for the migrations in the database. This table contains the ids of the migrations. If a migration version file was deleted, then Alembic wont be able to apply the migrations, and will show an error like this:

```bash
$ alembic stamp head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
ERROR [alembic.util.messaging] Can't locate revision identified by 'e67b5fb35b87'
  FAILED: Can't locate revision identified by 'e67b5fb35b87'
```

If this occures, one option is to just remove the versions table and redo the database migrations again (not recommended for procution code).

# Development Setup

## VSCode Configuration
This project includes VSCode configurations for an optimal development experience.

### Required Extensions
Install the following VSCode extensions:
- Python (`ms-python.python`)
- Pylance (`ms-python.vscode-pylance`)
- Docker (`ms-azuretools.vscode-docker`)
- GitLens (`eamodio.gitlens`)
- Python Docstring Generator (`njpwerner.autodocstring`)
- Better Comments (`aaron-bond.better-comments`)

The `.vscode/extensions.json` file will prompt you to install these when you open the project.

### Key Features
1. **Code Formatting**
   - Ruff for code formatting and linting (120 characters line length)
   - Format on save enabled

2. **Debugging**
   - Launch configurations for:
     - FastAPI local development
     - Docker container debugging
     - Test debugging
     - Current file debugging

3. **Tasks**
   Common tasks are available via Command Palette (`Ctrl/Cmd + Shift + P`):
   - `Tasks: Run Build Task` - Start development environment
   - `Tasks: Run Test Task` - Run tests
   - Other tasks: format code, type check, view logs

### Keyboard Shortcuts
- Format Document: `Shift + Alt + F`
- Run Tests: `Ctrl/Cmd + Shift + P` -> "Test: Run All Tests"
- Start Debugging: `F5`
- Toggle Terminal: `` Ctrl/Cmd + ` ``
- Quick Open File: `Ctrl/Cmd + P`

### Project Structure
The workspace settings are configured for:
- Python 3.11
- FastAPI development
- Docker-based development
- PostgreSQL database

### Snippets
Available snippets (trigger them by typing):
- `fastrouter`: Create new FastAPI router
- `pydmodel`: Create new Pydantic model
- `sqlmodel`: Create new SQLAlchemy model
- `repository`: Create new repository class
- `service`: Create new service class
- `pytest`: Create new test function

## Development Workflow
1. Start the development environment:
   ```bash
   make up
   ```

2. Access the application:
   - API: http://localhost:8080
   - Documentation: http://localhost:8080/docs

3. Run tests:
   ```bash
   make test
   ```

4. Format code:
   ```bash
   make format
   ```

5. Type checking:
   ```bash
   make typecheck
   ```

6. Run all checks:
   ```bash
   make check
   ```

## Code Style

This project uses:
- Ruff for linting and formatting
- MyPy for type checking
- The code follows standard Python style conventions through Ruff
