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

from ansiblereport.utils import *
from ansiblereport.model import *

class OutputModule:
    '''
    A simple plugin that displays report information to STDOUT.  Per
    requirements, it implements:

    name        Attribute with the name of the plugin
    do_report   Method that will take a list of events and report
                them in some manner.  It also takes an optional
                set of keyword arguments.
                The only optional keyword arguments that this
                plugin supports are:
                verbose         - Whether to be verbose in reporting
                smtp_subject    - Subject for email report
                smtp_recipient  - Recipient of email report
    '''
    name = 'email'

    def do_report(self, events, **kwargs):
        ''' take list of events and email them to recipient '''
        report = ''
        report_tasks = []
        if 'verbose' not in kwargs:
            kwargs['verbose'] = C.DEFAULT_VERBOSE
        for event in events:
            tasks = []
            if isinstance(event, AnsiblePlaybook):
                for task in event.tasks:
                    t = reportable_task(task, kwargs['verbose'])
                    if t is not None:
                        tasks.append(t)
                if tasks:
                    stats = AnsiblePlaybook.get_playbook_stats(event)
                    report += format_playbook_report(event, tasks, stats)
            elif isinstance(event, AnsibleTask):
                t = reportable_task(event, kwargs['verbose'])
                if t is not None:
                    report_tasks.append(t)
        if report_tasks:
            report += format_task_report(report_tasks, embedded=False)
        for arg in kwargs.keys():
            if not arg.startswith('smtp_'):
                del kwargs[arg]
        email_report(report, **kwargs)
