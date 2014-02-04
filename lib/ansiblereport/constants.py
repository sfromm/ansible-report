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
# along with ansible-report.  If not, see <http://www.gnu.org/licenses/>.

import datetime

import ansible.constants as AC

def get_config_value(key, env_var, default):
    ''' Look up key in ansible.cfg
    This uses load_config_file() and get_config() from ansible.constants
    '''
    config = AC.load_config_file()
    return AC.get_config(config, DEFAULT_SECTION, key, env_var, default)

DEFAULT_SECTION = 'ansiblereport'

DEFAULT_VERBOSE = False

DEFAULT_BACKOFF_START = get_config_value('backoff.start', None, 0.5)
DEFAULT_BACKOFF_MULT = get_config_value('backoff.mult', None, 1.05)
DEFAULT_BACKOFF_MAX = get_config_value('backoff.max', None, 60)

DEFAULT_DB_URI = get_config_value('sqlalchemy.url', 'ANSIBLEREPORT_DB_URI', 'sqlite://')

DEFAULT_STRFTIME = '%Y-%m-%d %H:%M:%S'
DEFAULT_SHORT_STRFTIME = '%H:%M:%S'
DEFAULT_FRIENDLY_STRFTIME = '%Y-%m-%d %H:%M'

DEFAULT_TASK_WARN_RESULTS = ['FAILED', 'ERROR', 'UNREACHABLE']
DEFAULT_TASK_OKAY_RESULTS = ['OK', 'SKIPPED', 'CHANGED']

DEFAULT_TASK_RESULTS = []
DEFAULT_TASK_RESULTS.extend(DEFAULT_TASK_OKAY_RESULTS)
DEFAULT_TASK_RESULTS.extend(DEFAULT_TASK_WARN_RESULTS)

DEFAULT_SMTP_SERVER = get_config_value('smtp.server', None, 'localhost')
DEFAULT_SMTP_SUBJECT = get_config_value('smtp.subject', None, 'ansible-report')
DEFAULT_SMTP_SENDER = get_config_value('smtp.sender', None, 'nobody@localhost')
DEFAULT_SMTP_RECIPIENT = get_config_value('smtp.recipient', None, 'root@localhost')

DEFAULT_OUTPUT = ['screen']
DEFAULT_OUTPUT_PLUGIN_PATH = AC.shell_expand_path(
        get_config_value('output_plugins',
            'ANSIBLEREPORT_OUTPUT_PLUGINS', '/usr/share/ansible-report/plugins'))
