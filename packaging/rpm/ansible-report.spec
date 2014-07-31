Name:       ansible-report
Version:	0.1
Release:	1%{?dist}
Summary:	Reporting tool for Ansible

Group:		Development/Libraries
License:	GPLv3
URL:		https://github.com/sfromm/ansible-report
#Source0:	https://github.com/sfromm/ansible-report/archive/release%{version}.tar.gz
Source0:	%{name}-%{version}.tar.gz

BuildArch:  noarch
BuildRequires:	python-devel
BuildRequires:  python-setuptools
Requires:   python-dateutil
#Requires:   python-peewee
Requires:   ansible
Provides: ansiblereport

%description
A utility to record events in a database via ansible callbacks and then
report on them at a later date.

%prep
%setup -q

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --root=$RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{python_sitelib}/ansiblereport/*
%{python_sitelib}/ansible_report*egg-info
%{_bindir}/ansible-report
%{_datadir}/ansible_plugins/callback_plugins/ansiblereport-logger.py*
%{_datadir}/ansible-report/plugins/*py*
%{_datadir}/ansible-report/*py*
%{_datadir}/ansible-report/migrations/*py*
%doc README.md COPYING

%changelog
* Tue Jul 29 2014 Stephen Fromm <sfromm gmail com>
- Tweaks to %files section

* Fri Jun 21 2013 Stephen Fromm <sfromm gmail com>
- Fixes to RPM spec to be consistent with name usage.

* Thu May  2 2013 Stephen Fromm <sfromm gmail com> - 0.1-0
- Initial version
