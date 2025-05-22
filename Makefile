.PHONY: setup test clean

# Virtual environment
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
PYTEST = $(VENV)/bin/pytest

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e .[dev]

test:
	$(PYTEST) tests/ -v --cov=sqlproxy

clean:
	rm -rf $(VENV)
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete