Ansible-Report Changelog
========================

## 0.2

* SCHEMA CHANGE: Add _changed_ column to _task_ table.
* Change to [peewee](https://github.com/coleifer/peewee) ORM to simplify
  requirements.
* Add logstalgia output plugin
* Add man pages to document output plugins and *ansible-report*.
* Simplify model.py so that it is just how the data is modeled in the
  database
* Extend manager.py to handle the helper methods for working with the
  database.
* Overhaul how tests are done.
* Add manage.py and migrations/ to handle migrations as schema changes happen.


## 0.1

Initial release.

* Uses [sqlalchemy](http://www.sqlalchemy.org/) for database ORM.
* Includes output plugins email and screen.
