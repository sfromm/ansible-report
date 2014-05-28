ansible-report Changelog
========================

## 0.2

* *SCHEMA CHANGE*: Add _changed_ column to _task_ table.
* *CONFIGURATION CHANGE*:  The parameter _sqlalchemy.url_ is no longer
   accepted.  Please update your configuration to use _db.driver_,
   _db.name_, _db.user_, and _db.passwd_ as appropriate.
* Change to [peewee](https://github.com/coleifer/peewee) ORM to simplify
  requirements.
* Add logstalgia output plugin
* Add man pages to document output plugins and *ansible-report*.
* Simplify model.py so that it is just how the data is modeled in the
  database
* Extend manager.py to handle the helper methods for working with the
  database.
* Add logging module to log the work of ansible-report and peewee.
* The configuration parameter _logdest_ can be used to control what file
  the log data is written to.  The parameter _loglevel_ can be used to
  control the logging verbosity.
* Overhaul how tests are done.
* Add manage.py and migrations/ to handle migrations as schema changes happen.

[View Changes](https://github.com/sfromm/ansible-report/compare/0.1...0.2)

## 0.1

Initial release.

* Uses [sqlalchemy](http://www.sqlalchemy.org/) for database ORM.
* Includes output plugins email and screen.
