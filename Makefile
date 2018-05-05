test: mypy check
	pytest tests


mypy:
	mypy async_timeout tests


check:
	python setup.py check -rms
