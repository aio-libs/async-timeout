SOURCES = setup.py async_timeout tests

test: lint
	pytest tests


lint: mypy check black


mypy:
	mypy --config-file setup.cfg async_timeout tests


black:
	isort -c -rc $(SOURCES)
	black --check $(SOURCES)
	flake8 $(SOURCES)


fmt:
	isort -rc $(SOURCES)
	black $(SOURCES)


check:
	python setup.py check -rms
