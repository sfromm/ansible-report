# Written by Stephen Fromm <sfromm@gmail.com>
# (C) 2013 University of Oregon
#
# This file is part of ansible-report
#
# ansible-report is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ansible-report is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import socket

DEFAULT_STRFTIME = '%Y-%m-%d %H:%M:%S'
DEFAULT_SHORT_STRFTIME = '%H:%M:%S'
DEFAULT_FRIENDLY_STRFTIME = '%Y-%m-%d %H:%M'

DEFAULT_TASK_WARN_RESULTS = ['FAILED', 'ERROR', 'UNREACHABLE']
DEFAULT_TASK_OKAY_RESULTS = ['OK', 'SKIPPED', 'CHANGED']

DEFAULT_TASK_RESULTS = []
DEFAULT_TASK_RESULTS.extend(DEFAULT_TASK_OKAY_RESULTS)
DEFAULT_TASK_RESULTS.extend(DEFAULT_TASK_WARN_RESULTS)

DEFAULT_SMTP_SERVER = 'localhost'
DEFAULT_SMTP_SUBJECT = 'ansible-report: {0}'.format(
        datetime.datetime.now().strftime(DEFAULT_FRIENDLY_STRFTIME))
DEFAULT_SMTP_SENDER = 'nobody@{0}'.format(socket.getfqdn())
DEFAULT_SMTP_RECIPIENT = 'root@{0}'.format(socket.getfqdn())
