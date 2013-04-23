ansible-report
==============

Utility to log and report Ansible activity

For information on *Ansible*, see http://ansible.cc.

Requirements
============

* [Ansible](http://ansible.cc)
* [SQLAlchemy](http://www.sqlalchemy.org/)
* [Alembic](https://pypi.python.org/pypi/alembic)

Callback Configuration
======================

To configure the callback plugin, place the file
_ansiblereport-logger.py_ in the directory where you have *ansible*
configured to look for callback plugins.  The default location for this
is typically:

    /usr/share/ansible_plugins/callback_plugins

Alternatively, you can configure this directory via your _ansible.cfg_.
After copying there, you need to configure the sqlalchemy url that will
be used.  The following is an example that uses a *sqlite* file in the
current directory:

    [ansiblereport]
    sqlalchemy.url = sqlite:///ansbile.sqlite

For information on configuring sqlaclhemy, one starting point is
[SQLAlchemy Engines](http://docs.sqlalchemy.org/en/latest/core/engines.html).  More information is available at http://docs.sqlalchemy.org/en/latest/.

Schema Migrations
=================

At this time, the database schema is not finalized.  While I will
endeavor to provide a mechanism to keep up with schema changes, I make no
guarantees at this time.  Migrations will be handled with
[alembic](http://alembic.readthedocs.org/en/latest/index.html).  Please
refer to _alembic_ documentation for how to handle migrations.  In the
simple case, you should be able to do:

    $ alembic upgrade head

In order to configure alembic, you should update the _sqlalchemy.url_
key in _alembic.ini_.
