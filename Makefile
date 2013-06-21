NAME = 'ansible-report'
PYTHON=python

VERSION := $(shell grep __version lib/ansiblereport/__init__.py | sed -e 's|^.*= ||' -e "s|'||g" )

# Get the branch information from git
ifneq ($(shell which git),)
GIT_DATE := $(shell git log -n 1 --format="%ai")
endif

ifeq ($(OS), FreeBSD)
DATE := $(shell date -j -f "%Y-%m-%d %H:%M:%s"  "$(GIT_DATE)" +%Y%m%d%H%M)
else
ifeq ($(OS), Darwin)
DATE := $(shell date -j -f "%Y-%m-%d %H:%M:%S"  "$(GIT_DATE)" +%Y%m%d%H%M)
else
DATE := $(shell date --utc --date="$(GIT_DATE)" +%Y%m%d%H%M)
endif
endif


# RPM build parameters
RPMSPECDIR = packaging/rpm
RPMSPEC = $(RPMSPECDIR)/$(NAME).spec
RPMDIST = $(shell rpm --eval '%dist')
RPMRELEASE = 1
ifeq ($(OFFICIAL),)
RPMRELEASE = 0.git$(DATE)
endif
RPMNVR = "$(NAME)-$(VERSION)-$(RPMRELEASE)$(RPMDIST)"


all: clean python

test:
	PYTHONPATH=lib nosetests -d -v --with-coverage \
		   --cover-erase --cover-package=ansiblereport

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
	@echo "make rpmcommon"
	@mkdir -p rpm-build
	@cp dist/*.gz rpm-build/
	@echo '$(VERSION)'
	@sed -e 's/^Version:.*/Version: $(VERSION)/' \
		-e 's/^Release:.*/Release: $(RPMRELEASE)%{?dist}/' \
		$(RPMSPEC) > rpm-build/$(NAME).spec

srpm: rpmcommon
	@echo make srpm
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %{_topdir}" \
	-bs rpm-build/$(NAME).spec
	@rm -f rpm-build/$(NAME).spec
	@echo "$(NAME) SRPM is built:"
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
	@echo "$(NAME) RPM is built:"
	@echo "    rpm-build/noarch/$(RPMNVR).noarch.rpm"

