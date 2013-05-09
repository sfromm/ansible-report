ansible-report
==============

Utility to log and report Ansible activity

For information on *Ansible*, see http://ansible.cc.

Requirements
============

* [Ansible](http://ansible.cc) >= 1.2
* [SQLAlchemy](http://www.sqlalchemy.org/)
* [Alembic](https://pypi.python.org/pypi/alembic)
* [python-dateutil](http://labix.org/python-dateutil)

Example Output
==============

Here is an example output:

    $ ansible-report --email --screen
    =================== Playbooks ====================

    /var/lib/ansible/audit.yml: 
            User: sfromm (sfromm)
      Start time: 2013-05-02 10:36:02
        End time: 2013-05-02 10:36:06

      --------- Tasks ---------

      10:36:02 gandalf.example.net command: OK

      -------- Summary --------

      gandalf.example.net   : ok=3  changed=1  error=0  failed=0  skipped=0  unreachable=0  


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

Report Configuration
====================

The only configuration related to reporting is the necessary SMTP
settings.  These are:

    [ansiblereport]
    smtp.server = localhost
    smtp.subject = ansible-report
    smtp.sender = nobody@example.net
    smtp.recipient = root@example.net

The _smtp.server_ setting is what *ansible-report* will connect to when
sending an email report to the configured recipients.

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

*Note*:  If you are using SQLite, please be aware that it has limited
abilities to [alter tables] [1].  You should also refer to Alembic's
[note] [2] on the subject.

  [1]: http://www.sqlite.org/lang_altertable.html
  [2]: https://bitbucket.org/zzzeek/alembic
