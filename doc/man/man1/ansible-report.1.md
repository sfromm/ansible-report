ANSIBLE-REPORT
==============

NAME
----
ansible-report - Utility to report on tasks performed by *Ansible*

SYNOPSIS
--------
ansible-report [options]

DESCRIPTION
-----------
*ansible-report* comes with a callback plugin that can be used to log
*Ansible's* tasks to a database for later auditing.  *ansible-report*
itself is used to query the database for later reporting purposes.
*ansible-report* uses output plugins to determine how to display the
report data.  This can be email, STDOUT, or something else of your
choosing.

OPTIONS
-------

*--version*

Display version number and exit.

*-v*, *--verbose*

Be verbose in how *ansible-report* runs.  Some output plugins may also
use this to determine what tasks to report.

*-o*, *--output*

Specify which output plugin to use.  Default is _screen_.

*-e* EXTRA_ARGS, *--extra-args*=EXTRA_ARGS

Set additional _key=value_ parameters that are passed to output
plugins.  See the respective man pages for plugins for what can be
passed.

*--prune*

Prune old events from the database.  Requires the `--age` option.

*--stats*

Only summarize the reportable data with statistics.  Do not report
details on individual tasks.

*-l* LIMIT, *--limit*=LIMIT

Limit reported events to LIMIT, an integer.  The default can be defined
in `ansible.cfg`.

*--age*=AGE

Query for tasks or playbooks that are no older than this date string.
You can either specify a _datetime_ string or something like: _N seconds
ago_, _N minutes ago_, _N hours ago_, _N days ago_, or _N weeks ago_.

*--uid*=UUID

Query for a playbook with the supplied UUID.  The UUID is assigned by
the callback plugin.

*--path*=PATH

Query for playbooks with the supplied PATH.

*--connection*=CONNECTION

Query for playbooks that used the supplied connection type.

*-c*, *--changed*

Query for tasks that reported changed as part of their task result.

*-m* MODULE_NAME, *--module*=MODULE_NAME

Query for tasks that used the module MODULE_NAME.

*-n* HOSTNAME, *--hostname*=HOSTNAME

Query for tasks that ran on the host HOSTNAME.

*-r* RESULT, *--result*=RESULT

Query for task where the result matches the supplied RESULT.  This must
be a valid *Ansible* task result string.  This can be _OKAY_, _SKIPPED_,
_FAILED_, _ERROR_, or _UNREACHABLE_.
