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
# along with ansible-report.  If not, see <http://www.gnu.org/licenses/>.

import ansiblereport.constants as C
from ansiblereport.model import *
from ansiblereport.utils import *

import os
import sys
import functools
import logging
import operator
import peewee
import random
import time
import urlparse
import uuid

peewee_logger = logging.getLogger('peewee')
peewee_logger.addHandler(logging.StreamHandler())

def _db_error_decorator(callable):
    @functools.wraps(callable)
    def _wrap(self, *args, **kwargs):
        try:
            return callable(self, *args, **kwargs)
        except DatabaseError as e:
            logging.warn("caught database error exception; will try to proceed")
        except Exception as e:
            raise
    return _wrap

def _filter_query(clauses, cls, col, arg, timeop):
    if not hasattr(cls, col):
        logging.warn('%s does not have attribute %s', cls, col)
        return sql
    if isinstance(arg, list):
        clauses.append(getattr(cls, col) << arg)
    else:
        if isinstance(getattr(cls, col), peewee.DateTimeField):
            clauses.append(timeop(getattr(cls, col), arg))
        else:
            clauses.append(getattr(cls, col) == arg)
    return clauses

class Manager(object):
    ''' db manager object '''

    def __init__(self, **kwargs):
        ''' initialize manager object '''
        engine = C.DEFAULT_DB_ENGINE
        if 'engine' in kwargs:
            engine = kwargs['engine']
        name = C.DEFAULT_DB_NAME
        if 'name' in kwargs:
            name = kwargs['name']
        user = C.DEFAULT_DB_USER
        if 'user' in kwargs:
            user = kwargs['user']
        passwd = C.DEFAULT_DB_PASS
        if 'passwd' in kwargs:
            passwd = kwargs['passwd']

        self.engine = engine
        self.name = name

        if 'sqlite' in engine:
            database = SqliteDatabase(name, threadlocals=True)
        elif 'postgres' in engine:
            database = PostgresqlDatabase(name, user=user, password=password)
        elif 'mysql' in engine:
            database = MySQLDatabase(name, user=user, password=password)
        else:
            database = None
        DB_PROXY.initialize(database)
        self.database = database
        try:
            self.database.connect()
        except OperationalError as e:
            logging.error("failed to open database %s", name)
            raise
        self.create_tables()

    def create_tables(self):
        ''' create tables if they do not exist '''
        AnsibleTask.create_table(fail_silently=True)
        AnsibleUser.create_table(fail_silently=True)
        AnsiblePlaybook.create_table(fail_silently=True)

    @_db_error_decorator
    def execute(self, modquery, nocommit=False):
        ''' execute a model query; returns number of rows affected '''
        with self.database.transaction():
            r = modquery.execute()
        return r

    @_db_error_decorator
    def save(self, modinst, nocommit=False):
        ''' save an object '''
        with self.database.transaction():
            modinst.save()

    @_db_error_decorator
    def get_or_create(self, model, **kwargs):
        ''' get or create an object '''
        try:
            instance = model.get(**kwargs)
        except AnsibleUser.DoesNotExist:
            instance = model(**kwargs)
            self.save(instance)
        return instance

    def log_user(self):
        (username, euid) = get_user()
        if euid is None:
            euid = username
        return self.get_or_create(AnsibleUser, username=username, euid=euid)

    def log_task(self, host, module, result, data, playbook=None):
        changed = False
        user = self.log_user()
        if isinstance(data, dict) and 'changed' in data:
            changed = data['changed']
        task = AnsibleTask(
            hostname=host,
            module=module,
            result=result,
            data=data,
            changed=changed,
            user=user,
            playbook=playbook
        )
        self.save(task)
        return task

    def log_play(self, path, connection, starttime=None):
        user = self.log_user()
        pb_uuid = uuid.uuid1()
        checksum = git_version(path)
        play = AnsiblePlaybook(
            path=path,
            uuid=pb_uuid,
            checksum=checksum,
            connection=connection,
            user=user
        )
        if starttime is not None:
            play.starttime = starttime
        self.save(play)
        return play

    def find_tasks(self, args=None, limit=1, timeop=operator.lt, orderby=True):
        clauses = []
        if args is not None:
            for col in args:
                if hasattr(AnsibleTask, col):
                    clauses = _filter_query(clauses, AnsibleTask, col, args[col], timeop)
            results = AnsibleTask.select().where(*clauses)
        else:
            results = AnsibleTask.select()
        if limit and limit != 0:
            results.limit(limit)
        return results

    def find_playbooks(self, args=None, limit=1, timeop=operator.lt, orderby=True):
        clauses = []
        if args is not None:
            for col in args:
                if hasattr(AnsiblePlaybook, col):
                    clauses = _filter_query(clauses, AnsiblePlaybook, col, args[col], timeop)
            results = AnsiblePlaybook.select().where(*clauses)
        else:
            results = AnsiblePlaybook.select()
        if limit and limit != 0:
            results.limit(limit)
        return results

    def get_last_n_playbooks(self, *args, **kwargs):
        return self.find_playbooks(*args, **kwargs)

    @classmethod
    def get_task_stats(cls, task):
        results = { task.hostname : {} }
        for key in C.DEFAULT_TASK_RESULTS:
            results[task.hostname][key.lower()] = 0
            results[task.hostname]['changed'] = 0
        if task.changed:
            results[task.hostname]['changed'] += 1
        results[task.hostname][task.result.lower()] += 1
        return results

    @classmethod
    def get_playbook_stats(cls, playbook):
        results = {}
        for task in playbook.tasks:
            if task.hostname not in results:
                results[task.hostname] = {}
                for key in C.DEFAULT_TASK_RESULTS:
                    results[task.hostname][key.lower()] = 0
                    results[task.hostname]['changed'] = 0
            if task.changed:
                results[task.hostname]['changed'] += 1
            results[task.hostname][task.result.lower()] += 1
        return results

    def rm_tasks(self, args=None, timeop=operator.ge):
        ''' remove tasks from database '''
        if args is None:
            return None
        clauses = []
        for col in args:
            if hasattr(AnsibleTask, col):
                clauses = _filter_query(clauses, AnsibleTask, col, args[col], timeop)
        return self.execute( AnsibleTask.delete().where(*clauses) )

    def rm_playbooks(self, args=None, timeop=operator.ge):
        ''' remove playbooks from database '''
        if args is None:
            return None
        clauses = []
        for col in args:
            if hasattr(AnsiblePlaybook, col):
                clauses = _filter_query(clauses, AnsiblePlaybook, col, args[col], timeop)
        return self.execute( AnsiblePlaybook.delete().where(*clauses) )

    def vacuum(self):
        ''' run vacuum '''
        if self.engine in [ 'sqlite' ]:
            self.database.execute_sql('VACUUM')

    # The following is based on buildbot/master/buildbot/db/pool.py
    def run(self, callable, *args, **kwargs):
        backoff = C.DEFAULT_BACKOFF_START
        start = time.time()
        while True:
            try:
                try:
                    rv = callable(self.session, *args, **kwargs)
                    break
                except sqlalchemy.exc.OperationalError as e:
                    text = e.orig.args[0]
                    if not isinstance(text, basestring):
                        raise
                    if "Lost connection" in text \
                        or "database is locked" in text:

                        # raise exception if have retried too often
                        elapsed = time.time() - start
                        if elapsed > C.DEFAULT_BACKOFF_MAX:
                            raise

                        # sleep and retry
                        time.sleep(backoff)
                        backoff *= C.DEFAULT_BACKOFF_MULT
                        # try again
                        continue
                    else:
                        raise
                except Exception as e:
                    raise
            finally:
                pass
        return rv

