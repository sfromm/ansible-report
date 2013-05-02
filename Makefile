NAME = 'ansiblereport'
PYTHON=python

VERSION := $(shell grep __version lib/ansiblereport/__init__.py | sed -e 's|^.*= ||' -e "s|'||g" )

# RPM build parameters
RPMSPECDIR = packaging/rpm
RPMSPEC = $(RPMSPECDIR)/ansiblereport.spec
RPMDIST = $(shell rpm --eval '%dist')
RPMRELEASE = 1
RPMNVR = "$(NAME)-$(VERSION)-$(RPMRELEASE)$(RPMDIST)"

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

rpmcommon: sdist
	@mkdir -p rpm-build
	@cp dist/*.gz rpm-build/
	@echo '$(VERSION)'
	@sed -e 's/^Version:.*/Version: $(VERSION)/' \
		-e 's/^Release:.*/Release: $(RPMRELEASE)%{?dist}/' \
		$(RPMSPEC) > rpm-build/$(NAME).spec

srpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %{_topdir}" \
	-bs rpm-build/$(NAME).spec
	@rm -f rpm-build/$(NAME).spec
	@echo "ansiblereport SRPM is built:"
	@echo "    rpm-build/$(RPMNVR).src.rpm"

rpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %{_topdir}" \
	-ba rpm-build/$(NAME).spec
	@rm -f rpm-build/$(NAME).spec
	@echo "ansiblereport RPM is built:"
	@echo "    rpm-build/$(RPMNVR).noarch.rpm"

