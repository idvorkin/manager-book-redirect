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
    @echo "Installing dependencies from requirements.txt..."
    @uv pip install -r requirements.txt || (echo "Failed to install from requirements.txt" && exit 1)
    @echo "Installing development dependencies from requirements-dev.txt..."
    @uv pip install -r requirements-dev.txt || (echo "Failed to install from requirements-dev.txt" && exit 1)
    @echo "Installation complete. Activate the venv using 'source .venv/bin/activate'"
