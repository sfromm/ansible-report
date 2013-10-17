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

import json
import datetime
import logging
import operator

import ansiblereport.constants as C

from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.types import TypeDecorator, Text
from sqlalchemy.ext.declarative import declarative_base

import ansible.constants

class JSONEncodedDict(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

    def __repr__(self):
        return "JSONEncodedDict(%s)" % self.value

Base = declarative_base()

def filter_query(session, sql, cls, col, arg, timeop):
    clauses = []
    if not hasattr(cls, col):
        logging.warn('%s does not have the attribute %s' % (cls, col))
        return sql
    if isinstance(arg, list):
        for n in arg:
            clauses.append(getattr(cls, col) == n)
    else:
        # the time comparison is hard-coded for now.
        # FIXME: make this user controllable.
        if 'time' in col:
            clauses.append(timeop(getattr(cls, col), arg))
        else:
            clauses.append(getattr(cls, col) == arg)
    if sql is None:
        sql = session.query(cls).filter(or_(*clauses))
    else:
        sql = sql.filter(or_(*clauses))
    return sql

class AnsibleTask(Base):
    __tablename__ = 'task'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    hostname = Column(String)
    module = Column(String)
    result = Column(String)
    data = Column(JSONEncodedDict)
    user_id = Column(Integer, ForeignKey('user.id'))
    playbook_id = Column(Integer, ForeignKey('playbook.id'))
    __table_args__ = (
            Index('task_timestamp_idx', 'timestamp'),
            Index('task_hostname_idx', 'hostname'),
            Index('task_module_idx', 'module'),
            Index('task_result_idx', 'result')
            )

    def __init__(self, hostname, module, result, data):
        self.hostname = hostname
        self.module = module
        self.result = result
        self.data = data

    def __repr__(self):
        return "<AnsibleTask<'%s', '%s', '%s'>" % (self.hostname, self.module, self.result)

    def delete(self, session):
        ''' remove object from database '''
        session.delete(self)

    @classmethod
    def find_tasks(cls, session, args=None, limit=1, timeop=operator.gt):
        sql = None
        if args is not None:
            for col in args:
                if hasattr(cls, col):
                    sql = filter_query(session, sql, cls, col, args[col], timeop)
        if limit == 0:
            return sql.order_by(cls.timestamp.desc())
        else:
            return sql.order_by(cls.timestamp.desc()).limit(limit)

class AnsibleUser(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    euid = Column(Integer)
    __table_args__ = (
            Index('user_username_idx', 'username'),
            )

    tasks = relation("AnsibleTask", backref='user',
                     cascade='all, delete, delete-orphan')
    playbooks = relation("AnsiblePlaybook", backref='user',
                         cascade='all, delete, delete-orphan')

    def __init__(self, user, euid):
        self.username = user
        self.euid = euid

    def __repr__(self):
        return "<AnsibleUser<'%s (effective %s)'>" % (self.username, self.euid)

    def delete(self, session):
        ''' remove object from database '''
        session.delete(self)

    @classmethod
    def get_user(cls, session, username, euid=None):
        if euid is None:
            euid = username
        return session.query(cls).filter(
                and_(cls.username == username, cls.euid == euid))

class AnsiblePlaybook(Base):
    __tablename__ = 'playbook'

    id = Column(Integer, primary_key=True)
    path = Column(String)
    uuid = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    connection = Column(String)
    starttime = Column(DateTime, default=datetime.datetime.now)
    endtime = Column(DateTime, default=datetime.datetime.now)
    checksum = Column(String)
    __table_args__ = (
            Index('playbook_path_idx', 'path'),
            Index('playbook_uuid_idx', 'uuid'),
            Index('playbook_connection_idx', 'connection'),
            Index('playbook_starttime_idx', 'starttime')
            )

    tasks = relation("AnsibleTask", backref='playbook',
                     cascade='all, delete, delete-orphan')

    def __init__(self, uuid):
        self.uuid = uuid

    def __repr__(self):
        return "<AnsiblePlaybook<'%s', '%s'>" % (self.path, self.uuid)

    def delete(self, session):
        ''' remove object from database '''
        session.delete(self)

    @classmethod
    def by_id(cls, session, identifier):
        return session.query(cls).get(identifier)

    @classmethod
    def find_playbooks(cls, session, args=None, limit=1, timeop=operator.gt):
        sql = None
        if args is not None:
            for col in args:
                if hasattr(cls, col):
                    sql = filter_query(session, sql, cls, col, args[col], timeop)
        if limit == 0:
            return sql.order_by(cls.starttime.desc())
        else:
            return sql.order_by(cls.starttime.desc()).limit(limit)

    @classmethod
    def get_last_n_playbooks(cls, session, args=None, limit=1, timeop=operator.gt):
        sql = None
        if args is not None:
            for col in args:
                if hasattr(cls, col):
                    sql = filter_query(session, sql, cls, col, args[col], timeop)
        if sql is None:
            return []
        if limit == 0:
            return sql.order_by(cls.starttime.desc())
        else:
            return sql.order_by(cls.starttime.desc()).limit(limit)

    @classmethod
    def get_playbook_stats(cls, playbook):
        results = {}
        for task in playbook.tasks:
            if task.hostname not in results:
                results[task.hostname] = {}
                for key in C.DEFAULT_TASK_RESULTS:
                    results[task.hostname][key.lower()] = 0
                    results[task.hostname]['changed'] = 0
            if 'changed' in task.data and bool(task.data['changed']):
                results[task.hostname]['changed'] += 1
            results[task.hostname][task.result.lower()] += 1
        return results
