# Default command - lists available recipes
default:
    @just --list

# Run fast tests (e.g., for pre-commit hooks)
fast-test:
    @echo "Running fast tests..."
    @pytest test_modal_redirect.py

# Run all tests
test:
    @echo "Running all tests..."
    @pytest

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
