# Reference card for usual actions in development environment.
#
# For standard installation of django-adobesign, see INSTALL.
# For details about django-adobesign's development environment, see CONTRIBUTING.rst.
#
PIP = pip
TOX = tox
PROJECT = $(shell python -c "import setup; print setup.NAME")


.PHONY: help develop clean distclean maintainer-clean test documentation sphinx readme release demo


#: help - Display callable targets.
help:
	@echo "Reference card for usual actions in development environment."
	@echo "Here are available targets:"
	@egrep -o "^#: (.+)" [Mm]akefile  | sed 's/#: /* /'


#: develop - Install minimal development utilities.
develop:
	pip install tox
	pip install pytest
	pip install pytest-cov
	pip install flake8
	pip install -e . -e ./demo


#: demo - Install demo project.
demo: develop
	python demo/manage.py migrate adobesign


#: serve - Run development server for demo project.
serve:
	python demo/manage.py runsslserver


#: clean - Basic cleanup, mostly temporary files.
clean:
	find . -name '*.pyc' -delete
	find . -name '*.pyo' -delete


#: distclean - Remove local builds, such as *.egg-info.
distclean: clean
	rm -rf *.egg
	rm -rf *.egg-info


#: maintainer-clean - Remove almost everything that can be re-generated.
maintainer-clean: distclean
	rm -rf build/
	rm -rf dist/
	rm -rf .tox/


#: test - Run test suites.
test:
	pytest --cov=django_adobesign -vv

#: test-all - Run test suites with tox.
test-all:
	$(TOX)

#: lint - Run lint test.
lint:
	flake8 --exclude=migrations django_adobesign demo

#: documentation - Build documentation (Sphinx, README, ...)
documentation: sphinx readme


sphinx:
	$(TOX) -e sphinx


#: readme - Build standalone documentation files (README, CONTRIBUTING...).
readme:
	$(TOX) -e readme

release:
	pip install zest.releaser
	fullrelease
