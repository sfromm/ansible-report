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

# fancy way to get the right version of sqlalchemy on rhel6
# in case pkg_resources has already been loaded.
def replace_dist(requirement):
    try:
        pkg_resources.require(requirement)
    except pkg_resources.VersionConflict:
        e = sys.exc_info()[1]
        dist = e.args[0]
        req = e.args[1]
        if dist.key == req.key and not dist.location.endswith('.egg'):
            del pkg_resources.working_set.by_key[dist.key]
            # We assume there is no need to adjust sys.path
            # and the associated pkg_resources.working_set.entries
            return pkg_resources.require(requirement)
replace_dist('SQLAlchemy >= 0.7')

import datetime
import os
import uuid
import socket
import ansiblereport.constants as C
from ansiblereport.manager import *
from ansiblereport.model import *
from ansiblereport.utils import *

class CallbackModule(object):
    """
    Callback module to log json blobs to sql
    """

    def __init__(self):
        self.uuid = uuid.uuid1()
        self.starttime = 0
        self.endtime = 0
        self.playbook = None
        self.mgr = Manager(C.DEFAULT_DB_URI)

    def _log_user(self):
        def fn(conn):
            (username, euid) = get_user()
            users = AnsibleUser.get_user(conn, username, euid)
            if users.count() > 0:
                user = users.all()[0]
            else:
                user = AnsibleUser(username, euid)
                conn.add(user)
                conn.commit()
            return user
        return self.mgr.run(fn)

    def _log_task(self, task):
        ''' add result to database '''
        def fn(conn):
            conn.add(task)
            user = self._log_user()
            task.user_id = user.id
            if self.playbook:
                task.playbook_id = self.playbook.id
            conn.commit()
        self.mgr.run(fn)

    def _log_play(self, play):
        ''' add play to database '''
        def fn(conn):
            conn.add(play)
            if play.user_id is None:
                user = self._log_user()
                play.user_id = user.id
            conn.commit()
        self.mgr.run(fn)

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        module = res['invocation']['module_name']
        self._log_task(AnsibleTask(host, module, 'FAILED', res))

    def runner_on_ok(self, host, res):
        module = res['invocation']['module_name']
        self._log_task(AnsibleTask(host, module, 'OK', res))

    def runner_on_error(self, host, msg):
        res = {}
        self._log_task(AnsibleTask(host, None, 'ERROR', res))

    def runner_on_skipped(self, host, item=None):
        res = {}
        self._log_task(AnsibleTask(host, None, 'SKIPPED', res))

    def runner_on_unreachable(self, host, res):
        if not isinstance(res, dict):
            res2 = res
            res = {}
            res['msg'] = res2
        self._log_task(AnsibleTask(host, None, 'UNREACHABLE', res))

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res, jid, clock):
        pass

    def runner_on_async_ok(self, host, res, jid):
        pass

    def runner_on_async_failed(self, host, res, jid):
        self._log_task(AnsibleTask(host, None, 'ASYNC_FAILED', res))

    def playbook_on_start(self):
        # start of playbook, no attrs are set yet
        self.starttime = datetime.datetime.now()
        self.playbook = AnsiblePlaybook(str(self.uuid))

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
                play.playbook.basedir, play.playbook.filename))
            self.playbook.path = path
            self.playbook.checksum = git_version(path)
            self.playbook.connection = play.playbook.transport
        self._log_play(self.playbook)

    def playbook_on_stats(self, stats):
        self.endtime = datetime.datetime.now()
        self.playbook.endtime = self.endtime
        self._log_play(self.playbook)
