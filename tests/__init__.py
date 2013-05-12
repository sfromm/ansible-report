#!/usr/bin/python

import sys
import pkg_resources

# fancy way to get the right version of sqlalchemy on rhel6 and
# still have nosetests work.
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

import ansiblereport
import ansiblereport.constants as C
from ansiblereport.model import *
from ansiblereport.utils import *

from ansible import callbacks
from ansible import runner

ALEMBIC_INI = os.path.join(os.path.dirname(__file__), 'alembic.test.ini')
ANSIBLE_CFG = os.path.join(os.path.dirname(__file__), 'ansible.cfg')
os.environ['ANSIBLE_CONFIG'] = ANSIBLE_CFG

class TestModel(unittest.TestCase):

    def test_create_db(self):
        session = init_db_session(alembic_ini=ALEMBIC_INI, debug=False)
        session.commit()
        self.assertEqual(session.connection().engine.name, 'sqlite')

class TestPlugin(unittest.TestCase):

    def setUp(self):
        self.user = getpass.getuser()
        self.module = 'ping'
        self.limit = 1
        self.callbacks = callbacks.DefaultRunnerCallbacks()
        self.runner = runner.Runner(
                module_name=self.module,
                module_args='',
                remote_user=self.user,
                remote_pass=None,
                host_list='tests/hosts',
                timeout=5,
                forks=1,
                background=0,
                pattern='all',
                transport='local',
                callbacks=self.callbacks
                )
        self.session = init_db_session(alembic_ini=ALEMBIC_INI, debug=False)

    # from ansible TestRunner.py
    def _run(self, module_name, module_args):
        self.runner.module_name = module_name
        args = ' '.join(module_args)
        self.runner.module_args = args
        results = self.runner.run()
        # when using nosetests this will only show up on failure
        # which is pretty useful
        print "RESULTS=%s" % results
        assert "localhost" in results['contacted']
        return results['contacted']['localhost']

    def test_module_callback(self):
        result = self._run(self.module, [])
        assert 'ping' in result

    def test_module_callback_data(self):
        clauses = []
        clauses.append(AnsibleTask.module == self.module)
        results = AnsibleTask.find_tasks(self.session,
                limit=self.limit, clauses=clauses)
        for r in results:
            self.assertEqual(r.module, self.module)
