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

import ansiblereport.constants as C

from peewee import *
from playhouse.proxy import Proxy

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

DB_PROXY = Proxy()

class BaseModel(Model):
    class Meta:
        database = DB_PROXY

class AnsibleUser(BaseModel):
    username = CharField(index=True)
    euid     = CharField()

    class Meta:
        db_table = 'user'

class AnsiblePlaybook(BaseModel):
    path       = CharField(index=True, null=True)
    uuid       = CharField(index=True)
    user       = ForeignKeyField(AnsibleUser, related_name='playbooks', on_delete='CASCADE')
    connection = CharField(index=True)
    checksum   = CharField(null=True)
    starttime  = DateTimeField(default=datetime.datetime.now, index=True)
    endtime    = DateTimeField(default=datetime.datetime.now, index=True)

    class Meta:
        db_table = 'playbook'
        order_by = ('-endtime', '-starttime')

class AnsibleTask(BaseModel):
    hostname  = CharField(index=True)
    module    = CharField(index=True, null=True)
    result    = CharField(index=True)
    changed   = BooleanField(index=True, default=False)
    timestamp = DateTimeField(default=datetime.datetime.now, index=True)
    user      = ForeignKeyField(AnsibleUser, related_name='tasks', on_delete='CASCADE')
    playbook  = ForeignKeyField(AnsiblePlaybook, related_name='tasks', null=True, on_delete='CASCADE')
    data      = JSONField(null=True)

    class Meta:
        db_table = 'task'
        order_by = ('-timestamp',)
