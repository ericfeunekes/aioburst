
.PHONY: build release install install-dev

build: 
	poetry build

release: build
	poetry publish -u __token__ -p $$PYPI_PASSWORD
	

dist/%.whl:
	${MAKE} build

install: dist/*.whl
	pip install $<

install-dev: 
	pip install -e .

uninstall:
	pip uninstall aioburst

upload-%: dist/*.whl
	gh release upload $* $<