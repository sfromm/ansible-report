ANSIBLEREPORT.EMAIL(3)
=======================

NAME
----
email - Email output plugin for ansible-report

SYNOPSIS
--------
ansible-report -o email [options]

DESCRIPTION
-----------

This will report the *ansible-report* query via email.  Similar to the
_screen_ plugin, the output is generally modeled on Logwatch
(http://www.logwatch.org).  This output plugin defaults to reporting
what has changed or if the task result is _FAILED_, _ERROR_, or
_UNREACHABLE_.  For each reported task, this plugin reports the
timestamp the task ran, whether a change occurred, the user the task ran
as, the corresponding playbook, and arguments to the task.

The email subject, sender, recipient, and SMTP server are defined in
`ansible.cfg`.  There you can define the following (default
values are also listed):

    [ansiblereport]
    smtp.server    = localhost
    smtp.recipient = root@localhost
    smtp.sender    = nobody@localhost
    smtp.subject   = ansible-report

OPTIONS
-------

*-v*, *--verbose*

Report on all tasks, including those that had no change or reported a
task result of _OK_ or _SKIPPED_.

*--stats*

Only summarize the reported tasks with statistics of ok, changed, error,
failed, skipped, and unreachable.  Do not print details about any
specific task.

COPYRIGHT
---------

Copyright, 2014, University of Oregon

*ansible-report* is released under the terms of the GPLv3 License.
