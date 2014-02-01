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
import ansiblereport.constants as C
from datetime import datetime, tzinfo
from dateutil.tz import *
import sys
import os.path
import ansible.utils

class OutputModule:
    '''
    A plugin that creates log format acceptable for logstalgia and pipes
    into logstalgia for visualization.
    requirements, it implements:

    name        Attribute with the name of the plugin
    do_report   Method that will take a list of events and report
                them via logstalgia visualization.
                The only optional keyword arguments that this
                plugin supports are:
                logstalgia_opts      - Additional options to pass to
                                       logstalgia

    This uses NCSA common log format:
    %h %l %u %t \"%r\" %s %b

    In this case, the following substitutions are made:
    %r is the module name and module_args
    '''
    name = 'logstalgia'
    STRFTIME_FORMAT = '%s'

    def _get_module_category(self, module):
        ''' look up a module's category '''
        path = ansible.utils.plugins.module_finder.find_plugin(module)
        if path is None:
            return 'NA'
        else:
            return os.path.basename(os.path.dirname(path))

    def _mk_custom_log(self, task):
        '''
        use logstalgia custom log format
        http://code.google.com/p/logstalgia/wiki/CustomLogFormat
        '''
        module_args = ''
        if task.data is not None:
            module_args += '/%s' % task.module
            if 'invocation' in task.data:
                if 'module_args' in task.data['invocation']:
                    args = task.data['invocation']['module_args']
                    if len(args) > 0:
                        module_args += '/%s' % args.replace(' ', '%20')
        ts = task.timestamp.replace(tzinfo=tzlocal())
        log = "{0}|{1}|{2}|{3}|{4}".format(
            ts.strftime(self.STRFTIME_FORMAT),
            task.hostname,
            module_args,
            task.result,
            '-'
        )
        return log

    def _format_group_match(self, category_set, category):
        ''' format the grouping option for logstalgia '''
        match = "^/(%s)" % ("|".join(category_set[category]))
        return "-g '{0},{1},15' ".format(category, match)

    def do_report(self, events, **kwargs):
        ''' take list of events and visualize via logstalgia '''
        logs = []
        modules = []
        hosts = []
        category = {}
        for event in events:
            if isinstance(event, AnsiblePlaybook):
                for task in event.tasks:
                    t = is_reportable_task(task, kwargs['verbose'])
                    if t is not None:
                        if task.module not in modules:
                            modules.append(task.module)
                        if task.hostname not in hosts:
                            hosts.append(task.hostname)
                        logs.append(self._mk_custom_log(task))
            elif isinstance(event, AnsibleTask):
                t = reportable_task(event, kwargs['verbose'])
                if t is not None:
                    if task.module not in modules:
                        modules.append(event.module)
                    if task.hostname not in hosts:
                        hosts.append(task.hostname)
                    logs.append(self._mk_event_log(event))
        if logs:
            logs.reverse()
            logs.append('\0')
            opts = ''
            if 'logstalgia_opts' in kwargs:
                opts += '%s ' % kwargs['logstalgia_opts']
            for m in modules:
                c = self._get_module_category(m)
                if m is None:
                    m = 'NA'
                if c in category:
                    if m not in category[c]:
                        category[c].append(m)
                else:
                    category[c] = [m]
            for c in sorted(category.keys()):
                # special case NA category
                if c != 'NA':
                    opts += self._format_group_match(category, c)
            c = 'NA'
            opts += self._format_group_match(category, c)
            cmd = 'logstalgia %s -' % opts
            rc, out, err = run_command(cmd, data='\n'.join(logs))
            if rc != 0:
                print >> sys.stderr, 'failed to run %s: %s %s' % (cmd, err, out)
                print >> sys.stderr, 'outputting logs to stdout for processing elsewhere'
                print '\n'.join(logs)
