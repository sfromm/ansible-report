#!/usr/bin/python

import json
import logging
from ansiblereport.model import *
from ansiblereport.manager import *

mgr = Manager()

def up():
    ''' add changed column to task '''
    with mgr.database.transaction():
        mgr.database.execute_sql("ALTER TABLE task ADD COLUMN changed SMALLINT default 0")
        logging.info("Updating changed column...")
        q = mgr.database.execute_sql("UPDATE task SET changed = 1 WHERE data LIKE '%changed\": true%'")
        logging.info("Updated changed column for %s tasks", 
                     mgr.database.rows_affected(q))

def down():
    ''' drop changed column from task '''
    with mgr.database.transaction():
        mgr.database.execute_sql("CREATE TABLE task_temp AS SELECT id, hostname, module, result, timestamp, user_id, playbook_id, data FROM task")
        mgr.database.execute_sql("DROP TABLE task")
        mgr.database.execute_sql("ALTER TABLE task_temp RENAME TO task")
        mgr.database.execute_sql("VACUUM")
