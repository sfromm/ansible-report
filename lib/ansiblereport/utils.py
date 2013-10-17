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

import os
import pwd
import smtplib
import subprocess
import traceback
import logging
import dateutil.parser
import datetime
import json

import ansiblereport.constants as C

import ansible.constants as AC

try:
    from email.mime.text import MIMEText
except ImportError:
    from email.MIMEText import MIMEText

def get_user():
    ''' return user information '''
    try:
        username = os.getlogin()
        euid = pwd.getpwuid(os.geteuid())[0]
        return (username, euid)
    except Exception, e:
        return (None, None)

def run_command(args, cwd=None, data=None):
    ''' run a command via subprocess '''
    if isinstance(args, list):
        shell = False
    else:
        shell = True
    rc = 0
    out = ''
    err = ''
    std_in = None
    if data:
        std_in = subprocess.PIPE
    try:
        cmd = subprocess.Popen(args, shell=shell, cwd=cwd,
                               close_fds=True,
                               stdin=std_in,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        out, err = cmd.communicate(input=data)
        rc = cmd.returncode
    except (OSError, IOError), e:
        logging.error("failed to run command: %s" % str(e))
        rc = e.errno
    except:
        logging.error("failed to run command: %s" % traceback.format_exc())
        rc = 257
    return (rc, out, err)

def git_version(path):
    ''' get git HEAD version for a repo '''
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

def pretty_json(arg, indent=4):
    return json.dumps(arg, sort_keys=True, indent=indent)

def format_task_brief(task, embedded=True):
    ''' summarize a task into a brief string '''
    strftime = C.DEFAULT_SHORT_STRFTIME
    if not embedded:
        strftime = C.DEFAULT_STRFTIME
    if task.module is None:
        return "{0} {1}: {2}".format(
                task.timestamp.strftime(strftime),
                task.hostname, task.result)
    else:
        return "{0} {1} {2}: {3}".format(
                task.timestamp.strftime(strftime),
                task.hostname, task.module, task.result)

def format_heading(title, subheading=True):
    if subheading:
        return '\n  {0:-^40}\n\n'.format(' {0} '.format(title))
    else:
        return '{0:=^60}\n\n'.format(' {0} '.format(title))

def format_playbook_report(playbook, tasks, stats):
    ''' take list of data and return formatted string '''
    report = ''
    report += format_heading('Playbook', subheading=False)
    report += "  {0:>10}: {1}\n".format('Path', playbook.path)
    report += "  {0:>10}: {1}\n".format('UUID', playbook.uuid)
    report += "  {0:>10}: {1} ({2})\n".format('User',
            playbook.user.username, playbook.user.euid)
    report += "  {0:>10}: {1}\n".format('Start time',
            playbook.starttime.strftime(C.DEFAULT_STRFTIME))
    report += "  {0:>10}: {1}\n".format('End time',
            playbook.endtime.strftime(C.DEFAULT_STRFTIME))

    if tasks:
        report += format_task_report(tasks)

    if stats:
        report += format_heading('Summary')
        for host, stats in stats.items():
            summary = ''
            if 'ok' in stats:
                summary += "{0}={1}  ".format('ok', stats['ok'])
            for stat in sorted(stats.keys()):
                if stat == 'ok':
                    continue
                summary += "{0}={1}  ".format(stat.lower(), stats[stat])
            report += "  {0:<20}: {1}\n".format(host, summary)
        report += "\n\n\n"
    return report

def format_task_report(tasks, embedded=True):
    ''' takes list of AnsibleTask and returns string '''
    report = ''
    report += format_heading('Tasks', subheading=embedded)
    for task in tasks:
        args = []
        report += "  {0}\n".format(format_task_brief(task, embedded))
        if 'invocation' not in task.data:
            report += '\n'
            continue
        invocation = task.data['invocation']
        module_name = task.data['invocation']['module_name']

        if 'changed' in task.data and bool(task.data['changed']):
            report += "    {0:>10}: {1}\n".format('Changed', 'yes')

        if not embedded:
            if task.user:
                args.append(('User', task.user.username))
            if task.playbook:
                args.append(('Playbook', task.playbook.path))

        if module_name == 'git':
            if 'after' in task.data:
                args.append(('SHA1', task.data['after']))
        elif module_name == 'copy' or module_name == 'file':
            if 'path' in task.data:
                args.append(('Path', task.data['path']))
            elif 'dest' in task.data:
                args.append(('Path', task.data['dest']))
        if invocation['module_args']:
            args.append(('Arguments', invocation['module_args']))
        if 'msg' in task.data and task.data['msg']:
            args.append(('Message', task.data['msg']))
        elif 'result' in task.data and task.data['result']:
            results = '\n'.join(task.data['result'])
            args.append(('Result', results))
        elif 'ansible_facts' in task.data:
            args.append(('Facts',
                         pretty_json(task.data['ansible_facts'], indent=8)))
        for arg in args:
            report += "    {0:>10}: {1}\n".format(arg[0], arg[1])
        report += '\n'
    return report

def is_reportable_task(task, verbose=False, embedded=True):
    ''' determine if task is reportable

    returns True if changed or failed
    returns True if okay and verbose is True
    otherwise returns False
    '''
    if task.result in C.DEFAULT_TASK_WARN_RESULTS:
        return True
    if task.result in C.DEFAULT_TASK_OKAY_RESULTS:
        if 'changed' in task.data and bool(task.data['changed']):
            return True
        if verbose:
            return True
    return False

def email_report(report_data,
        smtp_subject=C.DEFAULT_SMTP_SUBJECT,
        smtp_recipient=C.DEFAULT_SMTP_RECIPIENT):
    ''' pull together all the necessary details and send email report '''
    smtp_server = C.DEFAULT_SMTP_SERVER
    smtp_sender = C.DEFAULT_SMTP_SENDER
    msg = MIMEText(report_data)
    msg['Subject'] = smtp_subject
    msg['From'] = smtp_sender
    msg['To'] = smtp_recipient
    try:
        s = smtplib.SMTP(smtp_server)
        s.sendmail(smtp_sender, [smtp_recipient], msg.as_string())
        s.quit()
    except Exception, e:
        print 'failed to send email report: {0}'.format(str(e))
        return False
    return True

def parse_datetime_string(arg):
    ''' take string argument and convert to datetime object '''
    # if parsedatetime gets packaged, it could replace this
    # https://github.com/bear/parsedatetime
    try:
        date = dateutil.parser.parse(arg, default=True)
    except ValueError:
        parts = arg.split()
        if len(parts) == 1 and parts[0] == 'now':
            return datetime.datetime.now()
        elif len(parts) != 3 or parts[2] != 'ago':
            return None
        try:
            interval = int(parts[0])
        except ValueError:
            return None
        period = parts[1]
        if 'second' in period:
            delta = datetime.timedelta(seconds=interval)
        elif 'minute' in period:
            delta = datetime.timedelta(minutes=interval)
        elif 'hour' in period:
            delta = datetime.timedelta(hours=interval)
        elif 'day' in period:
            delta = datetime.timedelta(days=interval)
        elif 'week' in period:
            delta = datetime.timedelta(weeks=interval)
        date = datetime.datetime.now() - delta
    except:
        return None
    return date
