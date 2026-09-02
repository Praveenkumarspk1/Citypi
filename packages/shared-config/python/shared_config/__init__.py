"""
Shared Configuration - Python
Shared Python tooling configuration (Ruff, Pyright, pytest).
"""


def get_ruff_config() -> dict:
    """Return shared Ruff configuration."""
    return {
        "line-length": 120,
        "target-version": "py312",
        "select": [
            "E",   # pycodestyle errors
            "W",   # pycodestyle warnings
            "F",   # pyflakes
            "I",   # isort
            "B",   # flake8-bugbear
            "C4",  # flake8-comprehensions
            "UP",  # pyupgrade
            "SIM", # flake8-simplify
        ],
        "ignore": [
            "E501",  # line too long
            "B008",  # do not perform function calls in argument defaults
        ],
    }


def get_pyright_config() -> dict:
    """Return shared Pyright configuration."""
    return {
        "pythonVersion": "3.12",
        "typeCheckingMode": "strict",
        "reportMissingImports": True,
        "reportMissingTypeStubs": False,
    }


def get_pytest_config() -> dict:
    """Return shared pytest configuration."""
    return {
        "testpaths": ["tests"],
        "asyncio_mode": "auto",
        "addopts": "-v --tb=short",
    }
