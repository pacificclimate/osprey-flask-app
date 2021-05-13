# Configuration
APP_ROOT := $(abspath $(lastword $(MAKEFILE_LIST))/..)
APP_NAME := osprey-flask-app
VENV?=/tmp/osprey-flask-app-venv
PYTHON=${VENV}/bin/python3
PIP=${VENV}/bin/pip
export PIP_INDEX_URL=https://pypi.pacificclimate.org/simple

# Notebook targets
LOCAL_URL = http://localhost:5000
DEV_PORT ?= $(shell bash -c 'read -ep "Target port: " port; echo $$port')

# end of configuration

.PHONY: all
all: develop test-all clean-test

.PHONY: help
help:
	@echo "Please use 'make <target>' where <target> is one of:"
	@echo "  help              to print this help message. (Default)"
	@echo "  install           to install app by running 'pip install -e .'"
	@echo "  develop           to install with additional development requirements."
	@echo "  clean             to remove all files generated by build and tests."
	@echo "\nTesting targets:"
	@echo "  test              to run tests (but skip long running tests)."
	@echo "  test-all          to run all tests (including long running tests)."
	@echo "  lint              to run code style checks with flake8."
	@echo "\nSphinx targets:"
	@echo "  docs              to generate HTML documentation with Sphinx."
	@echo "\nDeployment targets:"
	@echo "  dist              to build source and wheel package."
	
## Build targets

.PHONY: install
install: venv
	@echo "Installing application ..."
	@-bash -c '${PIP} install -e .'

.PHONY: develop
develop: venv
	@echo "Installing development requirements for tests and docs ..."
	@-bash -c '${PIP} install -e ".[dev]"'
	
.PHONY: clean
clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

.PHONY: clean-build
clean-build:
	@echo "Removing build artifacts ..."
	@-rm -fr build/
	@-rm -fr dist/
	@-rm -fr .eggs/
	@-find . -name '*.egg-info' -exec rm -fr {} +
	@-find . -name '*.egg' -exec rm -f {} +
	@-find . -name '*.log' -exec rm -fr {} +
	@-find . -name '*.sqlite' -exec rm -fr {} +

.PHONY: clean-pyc
clean-pyc:
	@echo "Removing Python file artifacts ..."
	@-find . -name '*.pyc' -exec rm -f {} +
	@-find . -name '*.pyo' -exec rm -f {} +
	@-find . -name '*~' -exec rm -f {} +
	@-find . -name '__pycache__' -exec rm -fr {} +

.PHONY: clean-test
clean-test:
	@echo "Removing test artifacts ..."
	@-rm -fr .pytest_cache

.PHONY: clean-dist
clean-dist: clean
	@echo "Running 'git clean' ..."
	@git diff --quiet HEAD || echo "There are uncommitted changes! Aborting 'git clean' ..."
	## do not use git clean -e/--exclude here, add them to .gitignore instead
	@-git clean -dfx

.PHONY: venv
venv:
	test -d $(VENV) || python3 -m venv $(VENV)

## Test targets

.PHONY: test
test: venv
	@echo "Running tests (skip slow and online tests) ..."
	@bash -c '${PYTHON} -m pytest -v -m "not slow and not online" tests/'

.PHONY: test-all
test-all: venv
	@echo "Running all tests (including slow and online tests) ..."
	@bash -c '${PYTHON} -m pytest -v tests/'

.PHONY: lint
lint: venv
	@echo "Running black code style checks ..."
	@bash -c '${PYTHON} -m black . --check'

## Deployment targets

.PHONY: dist
dist: clean
	@echo "Building source and wheel package ..."
	@-python setup.py sdist
	@-python setup.py bdist_wheel
	@-bash -c 'ls -l dist/'
