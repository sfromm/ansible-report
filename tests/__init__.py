#!/usr/bin/python

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

import unittest
import getpass
import os
import multiprocessing

MAX_WORKERS = 75
ALEMBIC_INI = os.path.join(os.path.dirname(__file__), 'alembic.test.ini')
ANSIBLE_CFG = os.path.join(os.path.dirname(__file__), 'ansible.cfg')
os.environ['ANSIBLE_CONFIG'] = ANSIBLE_CFG
TEST_PLAYBOOK = 'tests/test_ansible_notify.yml'
TEST_TRANSPORT = 'local'
VERBOSITY = 0

import ansiblereport
import ansiblereport.constants as C
from ansiblereport.manager import *
from ansiblereport.model import *
from ansiblereport.utils import *

import ansible.runner as ans_runner
import ansible.playbook as ans_playbook
import ansible.callbacks as ans_callbacks

class TestModel(unittest.TestCase):

    def test_create_db(self):
        mgr = Manager(C.DEFAULT_DB_URI, debug=True)
        self.assertEqual(mgr.session.connection().engine.name, 'sqlite')

class TestPlugin(unittest.TestCase):

    def setUp(self):
        self.user = getpass.getuser()
        self.module_name = 'ping'
        self.module_args = []
        self.limit = 1
        self.host_list = 'tests/hosts'
        self.transport = TEST_TRANSPORT
        self.runner = None
        self.mgr = Manager(C.DEFAULT_DB_URI, debug=True)

    # from ansible TestRunner.py
    def _run_task(self, module_name='ping', module_args=[]):
        self.module_name = module_name
        self.module_args =  module_args
        runner_cb = ans_callbacks.DefaultRunnerCallbacks()
        self.runner = ans_runner.Runner(
                module_name=self.module_name,
                module_args=' '.join(self.module_args),
                remote_user=self.user,
                remote_pass=None,
                host_list=self.host_list,
                timeout=5,
                forks=1,
                background=0,
                pattern='all',
                transport=self.transport,
                callbacks=runner_cb,
                )
        results = self.runner.run()
        assert "localhost" in results['contacted']
        return results['contacted']['localhost']

    def _run_playbook(self, playbook):
        stats = ans_callbacks.AggregateStats()
        playbook_cb = ans_callbacks.PlaybookCallbacks(verbose=VERBOSITY)
        playbook_runner_cb = ans_callbacks.PlaybookRunnerCallbacks(stats, verbose=VERBOSITY)
        self.playbook = ans_playbook.PlayBook(
            playbook=playbook,
            host_list=self.host_list,
            forks=1,
            timeout=5,
            remote_user=self.user,
            remote_pass=None,
            extra_vars=None,
            stats=stats,
            callbacks=playbook_cb,
            runner_callbacks=playbook_runner_cb
            )
        result = self.playbook.run()
        return result

    def test_module_callback(self):
        ''' test runner module callback '''
        result = self._run_task()
        assert 'ping' in result

    def test_module_callback_data(self):
        ''' test runner module callback data '''
        def fn(conn):
            args = {}
            args['module'] = [self.module_name]
            results = AnsibleTask.find_tasks(conn, limit=self.limit, args=args)
            for r in results:
                self.assertEqual(r.module, self.module_name)
        return self.mgr.run(fn)

    def test_module_notify(self):
        ''' test handling of notify tasks '''
        # This greatly depends on what is defined in the playbook.
        results = self._run_playbook(TEST_PLAYBOOK)
        assert 'localhost' in results
        def fn(conn):
            args = {}
            args['module'] = 'command'
            results = AnsibleTask.find_tasks(conn, limit=self.limit, args=args)
            for r in results:
                self.assertEqual(r.data['invocation']['module_args'], 'uptime')
        return self.mgr.run(fn)

    def test_process_concurrency(self):
        ''' fork N processes and test concurrent writes to db '''
        workers = []
        for n in range(MAX_WORKERS):
            prc = multiprocessing.Process(target=self._run_task, args=())
            prc.start()
            workers.append(prc)

        for worker in workers:
            worker.join()
