test: lint
	python -m pytest tests

lint: fmt
	python -m mypy

fmt:
ifdef CI
	python -m pre_commit run --all-files --show-diff-on-failure
else
	python -m pre_commit run --all-files
endif


check:
	python -m build
	python -m twine check dist/*

install:
	python -m pip install --user -U pip
	python -m pip install --user -r requirements.txt
