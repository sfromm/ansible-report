# Written by Stephen Fromm <sfromm@gmail.com>
# (C) 2013-2014 University of Oregon
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
from ansiblereport.manager import *
from ansiblereport.model import *
import ansiblereport.constants as C

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

    def _update_stats(self, host, stats):
        if 'total' not in self.report_stats:
            self.report_stats['total'] = {}
        for key in stats:
            if key not in self.report_stats[host]:
                self.report_stats[host][key] = 0
            self.report_stats[host][key] += stats[key]
            if key not in self.report_stats['total']:
                self.report_stats['total'][key] = 0
            self.report_stats['total'][key] += stats[key]

    def do_report(self, events, **kwargs):
        ''' take list of events and email them to recipient '''
        self.report_stats = {}
        report = ''
        report_tasks = []
        if 'verbose' not in kwargs:
            kwargs['verbose'] = C.DEFAULT_VERBOSE
        if 'stats' not in kwargs:
            kwargs['stats'] = C.DEFAULT_STATS
        kwargs['verbose'] = bool(kwargs['verbose'])
        for event in events:
            tasks = []
            if isinstance(event, AnsiblePlaybook):
                for task in event.tasks:
                    if is_reportable_task(task, kwargs['verbose']):
                        tasks.append(task)
                if tasks:
                    stats = Manager.get_playbook_stats(event)
                    for host in stats:
                        self._update_stats(host, stats[host])
                    if not kwargs['stats']:
                        report += format_playbook_report(event, tasks, stats)
            elif isinstance(event, AnsibleTask):
                if is_reportable_task(event, kwargs['verbose']):
                    stats = Manager.get_task_stats(event)
                    self._update_stats(event.hostname, stats[event.hostname])
                    if not kwargs['stats']:
                        report_tasks.append(event)
        if report_tasks:
            report += format_task_report(report_tasks, embedded=False)
        if self.report_stats:
            totals = { 'total': self.report_stats.pop('total') }
            report += format_stats(self.report_stats, heading=False)
            report += format_stats(totals)
        for arg in kwargs.keys():
            if not arg.startswith('smtp_'):
                del kwargs[arg]
        if report:
            email_report(report, **kwargs)
