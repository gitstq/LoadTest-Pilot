.PHONY: help install test clean build lint format run-example

help:
	@echo "LoadTest-Pilot Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install      Install the package"
	@echo "  test         Run tests"
	@echo "  clean        Clean build artifacts"
	@echo "  build        Build distribution packages"
	@echo "  lint         Run linting"
	@echo "  format       Format code"
	@echo "  run-example  Run example load test"

install:
	pip install -e .

test:
	python -m pytest tests/ -v

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python setup.py sdist bdist_wheel

lint:
	python -m flake8 loadtest_pilot.py --max-line-length=120
	python -m pylint loadtest_pilot.py --disable=C,R

format:
	python -m black loadtest_pilot.py

run-example:
	python loadtest_pilot.py -u https://httpbin.org/get -c 5 -d 10
