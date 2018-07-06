test: mypy check
	pytest tests


mypy:
	mypy --config-file setup.cfg async_timeout tests


check:
	python setup.py check -rms
