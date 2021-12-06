test: lint
	pytest tests

lint: fmt
	mypy

fmt:
ifdef CI
	pre-commit run --all-files --show-diff-on-failure
else
	pre-commit run --all-files
endif


check:
	python -m build
	twine check dist/*

install:
	pip install -U pip
	pip install -r requirements.txt
