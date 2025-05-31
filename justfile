# Default command - lists available recipes
default:
    @just --list

# Run fast tests (e.g., for pre-commit hooks)
fast-test:
    @echo "Running fast tests in parallel..."
    @uv run pytest test_modal_redirect.py -n auto

# Run unit tests only
test:
    @echo "Running unit tests in parallel..."
    @uv run pytest test_modal_redirect.py -v -n auto

# Run E2E tests against deployed service
e2e-test:
    @echo "Running E2E tests against deployed Modal service in parallel..."
    @uv run pytest test_e2e_modal_redirect.py -v -n auto

# Run all tests (unit + E2E)
test-all:
    @echo "Running all tests (unit + E2E) in parallel..."
    @uv run pytest test_modal_redirect.py test_e2e_modal_redirect.py -v -n auto

# Deploy to Modal
deploy:
    @echo "Deploying to Modal..."
    @uv run modal deploy modal_redirect.py

# Serve locally with Modal
serve:
    @echo "Serving locally with Modal..."
    @uv run modal serve modal_redirect.py

# View Modal logs
logs:
    @echo "Viewing Modal logs..."
    @uv run modal app logs igor-blog

# Set up virtual environment and install dependencies
install:
    @echo "Setting up virtual environment and installing dependencies..."
    @echo "Attempting to create virtual environment using 'uv venv'..."
    @uv venv || (echo "Failed to create venv with uv. Ensure uv is installed and accessible." && exit 1)
    @echo "Virtual environment '.venv' created (or already existed)."
    @echo "To activate, run: source .venv/bin/activate"
    @echo "Installing project with development dependencies from pyproject.toml..."
    @uv pip install .[dev] || (echo "Failed to install project with dev dependencies using pyproject.toml" && exit 1)
    @echo "Installation complete. Activate the venv using 'source .venv/bin/activate'"
