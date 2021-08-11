help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests"
	#  @echo "docs - generate Sphinx HTML documentation, including API docs"
	#  @echo "confluence - build and publish the Sphinx Confluence documentation"
	@echo "deploy - package and upload a release to hashcat01"
	@echo "install - install the package to the user's Python's site-packages"
	@echo "help - show this help and exit"

deploy: hashcathelper.pyz
	@scp hashcathelper.pyz hashcat01:.local/bin/

hashcathelper.pyz: hashcathelper/
	@python3 -m zipapp hashcathelper -p python3

clean:
	@rm -rf build dist *.egg-info
	@find . -type f -name '*.pyc' -delete
	@find . -type d -name '__pycache__' | xargs rm -rf
	@rm -rf build/
	@rm -rf dist/
	@rm -rf .tox
	@rm -f src/*.egg*
	@rm -f hashcathelper.pyz

lint:
	@flake8 hashcathelper

test:
	@tox

docs:
	@echo "Not yet implemented"

install:
	python3 setup.py install --user

#  confluence:
#  	@make -C doc confluence

.PHONY: build clean lint test docs deploy install help confluence