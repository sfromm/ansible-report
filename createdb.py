#!/usr/bin/python

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import sys
from optparse import OptionParser
from ansiblereport.model import *

def main(args):
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option('-c', '--conf', default=None, help='path to alembic.ini')
    parser.add_option('-d', '--debug', action='store_true',
                      default=False, help='Debug mode')
    options, args = parser.parse_args()
    session = init_db_session(options.conf, options.debug)
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt, e:
        print >> sys.stderr, "error: %s" % str(e)
        sys.exit(1)
