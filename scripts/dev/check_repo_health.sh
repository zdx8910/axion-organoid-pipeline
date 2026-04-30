#!/usr/bin/env bash
set -euo pipefail

python -m pip install -e ".[dev,docs]"
ruff check
ruff format --check
mypy --strict src/
pytest -q --cov=meaorganoid --cov-report=term-missing --cov-fail-under=80
pytest --doctest-modules src/
pytest -q -m integration
mkdocs build --strict
python -m build
cffconvert --validate
