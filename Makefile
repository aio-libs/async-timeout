test: mypy check
	pytest tests


mypy:
	mypy --config-file mypy.ini async_timeout tests


check:
	python setup.py check -rms
