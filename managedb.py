#!/usr/bin/python

# Written by Stephen Fromm <stephenf nero net>
# (C) 2014 University of Oregon
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import datetime
import glob
import imp
import os
import logging
import sys
import time
from optparse import OptionParser
from ansiblereport.manager import *
import ansiblereport.constants as C

from peewee import CharField, DateTimeField, Model

class Migration(Model):
    ''' Migration model to track migration status '''
    migration = CharField()
    timestamp = DateTimeField(default=datetime.datetime.now)

def get_filenames(dir_name):
    files = []
    for path in glob.glob(os.path.join(dir_name, '*.py')):
        files.append(os.path.basename(path))
    return sorted(files, key=lambda fname: int(fname.split("_")[0]))

def _log_migration(model, name, direction):
    if direction == 'up':
        model.insert(migration=name).execute()
    else:
        model.delete().where(model.migration == name).execute()

def _do_migration(model, path, direction):
    if not os.path.exists(path):
        logging.error("Path %s does not exist; cannot perform migration", path)
        return None
    dir_name = os.path.dirname(path)
    name, ext = os.path.splitext(os.path.basename(path))

    migration_exists = model.select().where(model.migration == name).limit(1).exists()

    if migration_exists and direction == 'up':
        logging.warn("Migration %s already exists; skipping.", name)
        return False
    if not migration_exists and direction == 'down':
        logging.warn("Migration %s does not exist; skipping.", name)
        return False

    logging.debug("Loading migration %s", name)
    try:
        (fp, pathname, descr) = imp.find_module(name, [dir_name])
        try:
            module = imp.load_module(name, fp, pathname, descr)
        finally:
            fp.close()
    except Exception as e:
        logging.error("failed to load migration '%s': %s", name, str(e))
        return False

    if not hasattr(module, direction):
        logging.error("Migration %s does not implement %s migration", name, direction)
        return False
    logging.debug("Preparing migration %s", name)
    getattr(module, direction)()
    _log_migration(model, name, direction)
    return True

def migratedb(mgr, migration_path, direction, migration=None):
    migrations = []
    if not mgr.database:
        logging.error("Did not find database model object")
    model = Migration
    model._meta.database = mgr.database
    model.create_table(fail_silently=True)
    if os.path.isdir(migration_path):
        migrations = get_filenames(migration_path)
    if not migrations:
        logging.warn("No migrations found")
    if direction == 'down':
        migrations.reverse()

    if migration is not None:
        if migration not in migrations and '%s.py' not in migrations:
            logging.error("Could not find migration %s", migration)
            return False
        fname = os.path.join(migration_path, migration)
        if not os.path.exists(fname):
            fname += ".py"
        _do_migration(model, os.path.join(migration_path, fname), direction)
        return True

    for f in migrations:
        _do_migration(model, os.path.join(migration_path, f), direction)
    return True

def main(args):
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option('-m', '--migrations',
                      default=C.DEFAULT_MIGRATIONS_PATH,
                      help='Directory of migrations')
    parser.add_option('-d', '--direction', choices=['up', 'down'],
                      help='Migration direction: up or down')
    parser.add_option('-M', '--migration',
                      help='Only migrate up/down to this version')
    parser.add_option('-v', '--verbose', action="callback",
                      callback=increment_debug, default=C.DEFAULT_LOGLEVEL,
                      help='Be verbose.  Use more than once to increase verbosity')
    options, args = parser.parse_args()
    setup_logging('managedb')
    mgr = Manager()
    if not options.direction:
        logging.warn("Missing required argument 'up' or 'down'")
        return 1
    logging.warn("You are strongly encouraged to backup your database before proceeding")
    time.sleep(1.0)
    migratedb(mgr, options.migrations, options.direction, options.migration)

if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt, e:
        print >> sys.stderr, "error: %s" % str(e)
        sys.exit(1)
