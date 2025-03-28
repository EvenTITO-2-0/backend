# VSCode Setup Testing Plan

## 1. Extensions Installation
- [x] Open VSCode in the project
- [x] Check if VSCode prompts to install recommended extensions
- [x] Verify all extensions are installed:
  - [x] Python
  - [x] Pylance
  - [x] Black Formatter
  - [x] Docker
  - [x] GitLens
  - [x] Python Docstring Generator
  - [x] Better Comments

## 2. Editor Basic Features
- [ ] Check line length ruler (should be 120 chars)
- [ ] Test auto-save (modify file and wait 1 second)
- [ ] Verify file associations:
  - [ ] Open a .yaml file (should use YAML syntax)
  - [ ] Open Dockerfile (should use Dockerfile syntax)
  - [ ] Open .env file (should use dotenv syntax)
- [ ] Check if trailing whitespace is automatically trimmed
- [ ] Verify final newline is automatically added

## 3. Code Quality Tools
- [ ] Test Black formatting:
  - [ ] Write badly formatted Python code
  - [ ] Save file and check if it's formatted
- [ ] Test Ruff linting:
  - [ ] Write code with unused imports
  - [ ] Check if Ruff shows warnings
- [ ] Test MyPy type checking:
  - [ ] Write code with type hints missing
  - [ ] Run `make typecheck` to verify

## 4. Debugging Features
- [ ] Test FastAPI local debugging:
  - [ ] Set breakpoint in code
  - [ ] Start "FastAPI: Local" debug configuration
  - [ ] Verify breakpoint is hit
- [ ] Test Docker debugging:
  - [ ] Set breakpoint in code
  - [ ] Start "FastAPI: Docker" configuration
  - [ ] Verify breakpoint is hit
- [ ] Test debugging tests:
  - [ ] Set breakpoint in test file
  - [ ] Run "Python: Debug Tests"
  - [ ] Verify breakpoint is hit

## 5. Task Integration
- [ ] Test running tasks via Command Palette:
  - [ ] Start development environment (`make up`)
  - [ ] Run tests (`make test`)
  - [ ] Format code (`make format`)
  - [ ] Type check (`make typecheck`)
  - [ ] View logs (`make logs`)

## 6. Snippets
Test each snippet by typing the prefix and checking the output:
- [ ] `fastrouter` - FastAPI router
- [ ] `pydmodel` - Pydantic model
- [ ] `sqlmodel` - SQLAlchemy model
- [ ] `repository` - Repository class
- [ ] `service` - Service class
- [ ] `pytest` - Test function

## 7. Git Integration
- [ ] Check GitLens features:
  - [ ] Hover over line to see blame
  - [ ] Check blame heatmap in file
  - [ ] View file history
- [ ] Test source control features:
  - [ ] Make changes and see them in SCM view
  - [ ] Stage changes
  - [ ] Commit changes
  - [ ] Push changes

## 8. Python Environment
- [ ] Verify Python interpreter is correctly set
- [ ] Check if imports are working
- [ ] Verify IntelliSense suggestions
- [ ] Test environment variables loading

## Notes
- Mark each item as it's tested and working
- Document any issues found
- Note any configuration changes needed
