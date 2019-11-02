SOURCES = setup.py async_timeout tests

test: lint
	pytest tests


lint: mypy check black flake8


mypy:
	mypy --config-file setup.cfg async_timeout tests


black:
	isort -c -rc $(SOURCES)
	if python -c "import sys; sys.exit(sys.version_info < (3, 6))"; then \
	    black --check $(SOURCES); \
	fi

flake8:
	flake8 $(SOURCES)


fmt:
	isort -rc $(SOURCES)
	black $(SOURCES)


check:
	python setup.py check -rms
