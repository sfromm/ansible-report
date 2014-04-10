#!/usr/bin/python

import unittest
import getpass
import os
import multiprocessing

MAX_WORKERS = 75
ALEMBIC_INI = os.path.join(os.path.dirname(__file__), 'alembic.test.ini')
ANSIBLE_CFG = os.path.join(os.path.dirname(__file__), 'ansible.cfg')
os.environ['ANSIBLE_CONFIG'] = ANSIBLE_CFG
TEST_HOST_LIST = 'tests/hosts'
TEST_PLAYBOOK = 'tests/test_playbook.yml'
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

def _run_task(module_name='ping', module_args=[]):
    user = getpass.getuser()
    stats = ans_callbacks.AggregateStats()
    runner_cb = ans_callbacks.PlaybookRunnerCallbacks(stats, verbose=VERBOSITY)
    runner = ans_runner.Runner(
                module_name=module_name,
                module_args=' '.join(module_args),
                remote_user=user,
                remote_pass=None,
                host_list=TEST_HOST_LIST,
                timeout=5,
                forks=1,
                background=0,
                pattern='all',
                transport=TEST_TRANSPORT,
                callbacks=runner_cb,
                )
    results = runner.run()
    assert "localhost" in results['contacted']
    return results['contacted']['localhost']

class TestModel(unittest.TestCase):

    def setUp(self):
        self.user = getpass.getuser()
        self.module_name = 'ping'
        self.module_args = []
        self.limit = 1
        self.host_list = 'tests/hosts'
        self.runner = None

    def _run_playbook(self, playbook):
        stats = ans_callbacks.AggregateStats()
        playbook_cb = ans_callbacks.PlaybookCallbacks(verbose=VERBOSITY)
        playbook_runner_cb = ans_callbacks.PlaybookRunnerCallbacks(stats, verbose=VERBOSITY)
        self.playbook = ans_playbook.PlayBook(
            playbook=playbook,
            host_list=TEST_HOST_LIST,
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

    def test_create_db(self):
        self.mgr = Manager()
        self.assertEqual(isinstance(self.mgr.database, SqliteDatabase), True)

    def test_run_task(self):
        ''' run a task '''
        result = _run_task()
        assert 'ping' in result

    def test_run_task_playbook(self):
        ''' run a test playbook with notify '''
        results = self._run_playbook(TEST_PLAYBOOK)
        assert 'localhost' in results

class TestPlugin(unittest.TestCase):

    def setUp(self):
        self.mgr = Manager()
        self.user = getpass.getuser()
        self.module_name = 'ping'

    def test_check_playbook_data(self):
        ''' test playbook data is present '''
        playbook = self.mgr.find_playbooks(limit=1)
        self.assertEqual(isinstance(playbook[0], AnsiblePlaybook), True)

    def test_check_task_data(self):
        ''' test for task data '''
        args = {}
        args['module'] = self.module_name
        results = self.mgr.find_tasks(args=args)
        assert results.count() > 0
        for r in results:
            self.assertEqual(r.module, self.module_name)


class TestStressPlugin(unittest.TestCase):

    def test_process_concurrency(self):
        ''' fork N processes and test concurrent writes to db '''
        workers = []
        for n in range(MAX_WORKERS):
            prc = multiprocessing.Process(target=_run_task, args=())
            prc.start()
            workers.append(prc)

        for worker in workers:
            worker.join()
