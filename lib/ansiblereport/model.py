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

from peewee import *

import ansible.constants

class JSONField(CharField):
    ''' Custom JSON field '''

    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        try:
            return json.loads(value)
        except:
            return value

    def __repr__(self):
        return "JSONField(%s)" % self.value

database_proxy = Proxy()

class BaseModel(Model):
    class Meta:
        database = database_proxy

class Task(BaseModel):
    timestamp = DateTimeField(default=datetime.datetime.now)
    hostname  = CharField()
    module    = CharField()
    result    = CharField()
    changed   = BooleanField()
    data      = JSONField()
    user      = ForeignKeyField(User, related_name='tasks')
    playbook  = ForeignKeyField(Playbook, related_name='tasks')
    
    class Meta:
        db_table = 'task'
        indexes = (
            (('timestamp'), False),
            (('hostname'), False),
            (('module'), False),
            (('changed'), False),
            (('result'), False),
        )

class User(BaseModel):
    username = CharField()
    euid     = CharField()

    class Meta:
        db_table = 'user'
        indexes = ( (('username', 'euid'), True) )

class Playbook(BaseModel):
    path       = CharField()
    uuid       = CharField()
    user       = ForeignKeyField(User, related_name='playbooks')
    connection = CharField()
    starttime  = DateTimeField(default=datetime.datetime.now)
    endtime    = DateTimeField(default=datetime.datetime.now)
    checksum   = CharField()

    class Meta:
        db_table = 'playbook'
        indexes = (
            (('path'), False),
            (('uuid'), False),
            (('connection'), False),
            (('starttime'), False),
        )
