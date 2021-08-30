SOURCES = setup.py async_timeout tests

test: lint
	pytest tests


lint: mypy check black flake8


mypy:
	mypy


black:
	isort -c $(SOURCES)
	black --check $(SOURCES)

flake8:
	flake8 $(SOURCES)


fmt:
	isort $(SOURCES)
	black $(SOURCES)


check:
	python setup.py check -rms
