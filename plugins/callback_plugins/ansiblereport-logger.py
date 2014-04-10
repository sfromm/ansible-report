# Written by Stephen Fromm <sfromm@gmail.com>
# (C) 2013 University of Oregon

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

import sys
import pkg_resources


import datetime
import os
import socket
import ansiblereport.constants as C
from ansiblereport.manager import *

class CallbackModule(object):
    """
    Callback module to log json blobs to sql
    """

    def __init__(self):
        self.starttime = 0
        self.playbook = None
        self.mgr = Manager()

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        module = res['invocation']['module_name']
        task = self.mgr.log_task(host, module, 'FAILED', res, self.playbook)

    def runner_on_ok(self, host, res):
        module = res['invocation']['module_name']
        task = self.mgr.log_task(host, module, 'OK', res, self.playbook)

    def runner_on_error(self, host, msg):
        res = {}
        task = self.mgr.log_task(host, None, 'ERROR', res, self.playbook)

    def runner_on_skipped(self, host, item=None):
        res = {}
        task = self.mgr.log_task(host, None, 'SKIPPED', res, self.playbook)

    def runner_on_unreachable(self, host, res):
        if not isinstance(res, dict):
            res2 = res
            res = {}
            res['msg'] = res2
        task = self.mgr.log_task(host, None, 'UNREACHABLE', res, self.playbook)

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res, jid, clock):
        pass

    def runner_on_async_ok(self, host, res, jid):
        pass

    def runner_on_async_failed(self, host, res, jid):
        task = self.mgr.log_task(host, None, 'ASYNC_FAILED', res, self.playbook)

    def playbook_on_start(self):
        # start of playbook, no attrs are set yet
        self.starttime = datetime.datetime.now()
        self.playbook = None

    def playbook_on_notify(self, host, handler):
        ''' reports name of host and name of handler playbook will execute '''
        pass

    def on_no_hosts_matched(self):
        pass

    def on_no_hosts_remaining(self):
        pass

    def playbook_on_task_start(self, name, is_conditional):
        pass

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        pass

    def playbook_on_setup(self):
        pass

    def playbook_on_import_for_host(self, host, imported_file):
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        pass

    def playbook_on_play_start(self, pattern):
        play = getattr(self, 'play', None)
        if play is not None:
            path = os.path.abspath(os.path.join(
                play.playbook.basedir,
                os.path.basename(play.playbook.filename)
            ))
            self.playbook = self.mgr.log_play(
                path, play.playbook.transport, self.starttime
            )

    def playbook_on_stats(self, stats):
        self.playbook.endtime = datetime.datetime.now()
        self.mgr.save(self.playbook)
