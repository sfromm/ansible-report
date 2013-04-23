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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess
import traceback
import logging

def run_command(args, cwd=None):
    if isinstance(args, list):
        shell = False
    else:
        shell = True
    rc = 0
    out = ''
    err = ''
    try:
        cmd = subprocess.Popen(args, shell=shell, cwd=cwd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        out, err = cmd.communicate()
        rc = cmd.returncode
    except (OSError, IOError), e:
        logging.error("failed to run command: %s" % str(e))
        rc = e.errno
    except:
        logging.error("failed to run command: %s" % traceback.format_exc())
        rc = 257
    return (rc, out, err)

def git_version(path):
    version = 'NA'
    path_dir = os.path.dirname(path)
    (rc, out, err) = run_command(['git', 'rev-parse', '--git-dir'], cwd=path_dir)
    if rc != 0 or len(out) < 1:
        return version
    git_dir = out.rstrip('\n')
    f = open(os.path.join(git_dir, 'HEAD'))
    branch = f.readline().split('/')[-1].rstrip('\n')
    f.close()
    branch_path = os.path.join(git_dir, 'refs', 'heads', branch)
    if os.path.exists(branch_path):
        f = open(branch_path)
        version = f.readline()[:10]
        f.close()
    return version
