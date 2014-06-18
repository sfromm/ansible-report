# Written by Stephen Fromm <sfromm@gmail.com>
# (C) 2013-2014 University of Oregon

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
import sqlite3
import time
import urlparse
import uuid

peewee_logger = logging.getLogger('peewee')
peewee_logger.addHandler(logging.StreamHandler())

def _db_error_decorator(callable):
    '''
    decorator for catching errors when interacting with database.
    the ansible callbacks are run from multiple processes.  to deal
    with possible lock contention from these writers and sqlite, this
    uses a semaphore to control access to the database.  this should
    not be necessary with databases such as mysql or postgresql.
    '''
    @functools.wraps(callable)
    def _wrap(self, *args, **kwargs):
        try:
            lock = None
            if hasattr(self, 'engine') and self.engine == 'sqlite':
                path = os.path.join(os.path.dirname(self.name), ".ansiblereport-lock")
                lock = Lock(path)
                lock.acquire()
            result = callable(self, *args, **kwargs)
            if lock:
                lock.release()
            return result
        except sqlite3.OperationalError as exc:
            logging.warn("caught sqlite operational error exception: %s", str(exc))
        except DatabaseError as exc:
            logging.warn("caught database error exception; will try to proceed: %s", str(exc))
        except Exception as exc:
            raise
    return _wrap

def _build_clause(cls, col, val, timeop):
    clause = None
    if not hasattr(cls, col):
        logging.warn('%s does not have the attribute %s', cls, col)
        return clause
    logging.debug("building filter clause %s:%s", col, val)
    if isinstance(val, list):
        clause = getattr(cls, col) << val
    else:
        if isinstance(getattr(cls, col), peewee.DateTimeField):
            clause = timeop(getattr(cls, col), val)
        else:
            clause = getattr(cls, col) == val
    return clause

def _filter_query(cls, args, **kwargs):
    timeop = kwargs.get('timeop', operator.lt)
    intersection = kwargs.get('intersection', C.DEFAULT_INTERSECTION)
    clauses = []
    qry = None
    for col in args:
        clause = _build_clause(cls, col, args[col], timeop)
        if clause is None:
            continue
        clauses.append(clause)
        if intersection:
            if qry is None:
                qry = cls.select().where(*clauses)
            else:
                qry = qry.where(*clauses)
            clauses = []
    if not intersection:
        qry = cls.select().where(reduce(operator.or_, clauses))
    return qry

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
        r = modquery.execute()
        return r

    @_db_error_decorator
    def save(self, modinst, nocommit=False):
        ''' save an object '''
        modinst.save()

    @_db_error_decorator
    def get_or_create(self, model, **kwargs):
        ''' get or create an object '''
        try:
            logging.debug("checking if user '%s' already exists", kwargs['username'])
            instance = model.get(**kwargs)
        except AnsibleUser.DoesNotExist:
            logging.debug("user '%s' does not exist; creating", kwargs['username'])
            instance = model(**kwargs)
            instance.save()
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

    def find_tasks(self, args=None, limit=1, timeop=operator.ge):
        clauses = []
        logging.debug("preparing task query")
        if args is not None:
            qry = _filter_query(AnsibleTask, args, timeop=timeop)
        else:
            qry = AnsibleTask.select().naive()
        if limit and limit != 0:
            qry.limit(limit)
        logging.debug("performed task query")
        return qry

    def find_playbooks(self, args=None, limit=1, timeop=operator.ge):
        clauses = []
        logging.debug("preparing playbook query")
        if args is not None:
            qry = _filter_query(AnsiblePlaybook, args, timeop=timeop)
        else:
            qry = AnsiblePlaybook.select().naive()
        if limit and limit != 0:
            qry.limit(limit)
        logging.debug("performed playbook query")
        return qry

    def get_last_n_playbooks(self, *args, **kwargs):
        return self.find_playbooks(*args, **kwargs)

    @classmethod
    def get_task_stats(cls, task):
        results = { task.hostname: {} }
        results[task.hostname]['changed'] = 0
        for key in C.DEFAULT_TASK_RESULTS:
            results[task.hostname][key.lower()] = 0
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
                results[task.hostname]['changed'] = 0
                for key in C.DEFAULT_TASK_RESULTS:
                    results[task.hostname][key.lower()] = 0
            if task.changed:
                results[task.hostname]['changed'] += 1
            results[task.hostname][task.result.lower()] += 1
        return results

    def rm_tasks(self, args=None, timeop=operator.le):
        ''' remove tasks from database '''
        if args is None:
            return None
        clauses = []
        for col in args:
            if hasattr(AnsibleTask, col):
                c = _build_clause(AnsibleTask, col, args[col], timeop)
                if c is None:
                    continue
                clauses.append(c)
        return self.execute(AnsibleTask.delete().where(*clauses))

    def rm_playbooks(self, args=None, timeop=operator.le):
        ''' remove playbooks from database '''
        if args is None:
            return None
        clauses = []
        for col in args:
            if hasattr(AnsiblePlaybook, col):
                c = _build_clause(AnsiblePlaybook, col, args[col], timeop)
                if c is None:
                    continue
                clauses.append(c)
        return self.execute(AnsiblePlaybook.delete().where(*clauses))
