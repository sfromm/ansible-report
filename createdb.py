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

import sys
from optparse import OptionParser
from ansiblereport.manager import *

def main(args):
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option('-v', '--verbose', action="callback",
                      callback=increment_debug, default=C.DEFAULT_LOGLEVEL,
                      help='Be verbose.  Use more than once to increase verbosity')
    parser.add_option('-m', '--mode', type='int',
                      help='File permission/mode if SQLite')
    options, args = parser.parse_args()
    setup_logging('createdb')
    mgr = Manager()
    mgr.create_tables()
    if 'sqlite' in mgr.engine:
        mgr.database.execute_sql("PRAGMA journal_mode = wal")
        os.chmod(mgr.name, options.mode)
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt, e:
        print >> sys.stderr, "error: %s" % str(e)
        sys.exit(1)
