.PHONY: flake8 dist twine twine-test

ifeq ($(OS),Windows_NT)
ENVPATH := $(shell python -c "import os.path; import sys; print(os.path.join(sys.exec_prefix, 'Scripts'))")\
MOCKSPATH := tests\mocks;
else
ENVPATH := $(shell pipenv --venv)/bin/
MOCKSPATH := $(PWD)/tests/mocks:
endif

flake8:
	pipenv run flake8 --ignore=E501,W503,E203 *.py simplemonitor/

integration-tests:
	echo mocks path is $(MOCKSPATH)
	echo env path is $(ENVPATH)
	pipenv run env PATH="$(MOCKSPATH)$(PATH)" "$(ENVPATH)coverage" run monitor.py -1 -v -d -f tests/monitor.ini

env-test:
	pipenv run env TEST_VALUE=myenv "$(ENVPATH)coverage" run --append monitor.py -t -f tests/monitor-env.ini

unit-test:
	pipenv run "$(ENVPATH)coverage" run --append -m unittest discover -s tests

network-test:
	pipenv run tests/test-network.sh

dist:
	rm -f dist/simplemonitor-*
	pipenv run python setup.py sdist bdist_wheel

twine-test:
	pipenv run python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

twine:
	pipenv run python -m twine upload dist/*
