NAME = 'ansiblereport'
PYTHON=python

all: clean python

clean:
	@echo "Cleaning distutils leftovers"
	rm -rf build
	rm -rf dist
	@echo "Cleaning up byte compiled python files"
	find . -type f -regex ".*\.py[co]$$" -delete
	@echo "Cleaning up RPM build files"
	rm -rf MANIFEST rpm-build

python:
	$(PYTHON) setup.py build

install:
	$(PYTHON) setup.py install

sdist: clean
	$(PYTHON) setup.py sdist -t MANIFEST.in

pep8:
	@echo "Running PEP8 compliance tests"
	-pep8 -r --ignore=E501,E202,E302,E303 lib/ bin/ plugins/
