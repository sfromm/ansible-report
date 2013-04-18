ansible-report
==============

Utility to log and report ansible activity

At this time, the database schema is not finalized.  While I will
attempt to provide a mechanism to keep up with schema changes, I make no
guarantees at this time.

To configure the callback, configure something like the following in
your ansible.cfg:

    [ansiblreport]
    uri = sqlite:///ansbile.sqlite

This will create a sqlite db in your current working directory.  For
information on specifying a uri for sqlalchemy, please see the
appropriate documentation.
