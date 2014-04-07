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


import functools
import random
import time
import sqlalchemy
import os
import sys

def _db_error_decorator(callable):
    @functools.wraps(callable)
    def _wrap(self, *args, **kwargs):
        try:
            return callable(self, *args, **kwargs)
        except Exception as e:
            raise
    return _wrap

class Manager(object):
    ''' db manager object '''

    def __init__(self, uri, alembic_ini=None, debug=False):
        self.engine = create_engine(uri, echo=debug)
        Base.metadata.create_all(self.engine)
        if alembic_ini is not None:
            # if we have an alembic.ini, stamp the db with the head revision
            from alembic.config import Config
            from alembic import command
            alembic_cfg = Config(alembic_ini)
            command.stamp(alembic_cfg, 'head')
        Session = sessionmaker(bind=self.engine, autocommit=True)
        self.session = Session()

    @_db_error_decorator
    def save(self, model, nocommit=False):
        ''' save an object '''
        with self.session.begin(subtransactions=True):
            self.session.add(model)
            self.session.flush()

    def get_or_create(self, model, **kwargs):
        ''' get or create an object '''
        instance = self.session.query(model).filter_by(**kwargs).first()
        if not instance:
            instance = model(**kwargs)
            self.save(instance)
        return instance

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

