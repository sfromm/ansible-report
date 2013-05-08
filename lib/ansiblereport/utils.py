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
import smtplib
import subprocess
import traceback
import logging
import dateutil.parser
import datetime

import ansiblereport.constants as C

import ansible.constants as AC

try:
    from email.mime.text import MIMEText
except ImportError:
    from email.MIMEText import MIMEText

def run_command(args, cwd=None):
    ''' run a command via subprocess '''
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

def format_playbook_report(data):
    ''' take list of data and return formatted string '''
    report = ''
    report += '{0:=^50}\n\n'.format(' Playbooks ')
    for pb in data:
        report += "%s: \n" % pb['playbook'].path
        report += "  {0:>10}: {1} ({2})\n".format('User',
                pb['playbook'].user.username, pb['playbook'].user.euid)
        report += "  {0:>10}: {1}\n".format('Start time',
                pb['playbook'].starttime.strftime(C.DEFAULT_STRFTIME))
        report += "  {0:>10}: {1}\n".format('End time',
                pb['playbook'].endtime.strftime(C.DEFAULT_STRFTIME))

        if 'tasks' in pb:
            report += format_task_report(pb['tasks'])

        report += '\n  {0:-^25}\n\n'.format(' Summary ')
        for host, stats in pb['stats'].items():
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
    report = ''
    if len(tasks) < 1:
        return report
    report += '\n  {0:-^25}\n\n'.format(' Tasks ')
    for task in tasks:
        args = []
        report += "  {0}\n".format(task[0])
        if 'invocation' not in task[1]:
            report += '\n'
            continue
        invocation = task[1]['invocation']
        module_name = task[1]['invocation']['module_name']
        if module_name == 'setup':
            report += '\n'
            continue
        if 'changed' in task[1] and bool(task[1]['changed']):
            if 'module_name' == 'setup':
                continue
            report += "    {0:>10}: {1}\n".format('Changed', 'yes')

        if module_name == 'git':
            args.append(('SHA1', task[1]['after']))
        elif module_name == 'copy' or module_name == 'file':
            if 'path' in task[1]:
                args.append(('Path', task[1]['path']))
            elif 'dest' in task[1]:
                args.append(('Path', task[1]['dest']))
        if invocation['module_args']:
            args.append(('Arguments', invocation['module_args']))
        if 'msg' in task[1] and task[1]['msg']:
            args.append(('Message', task[1]['msg']))
        elif 'result' in task[1] and task[1]['result']:
            results = '\n'.join(task[1]['result'])
            args.append(('Result', results))
        for arg in args:
            report += "    {0:>10}: {1}\n".format(arg[0], arg[1])
        report += '\n'
    return report

def email_report(report_data, smtp_subject=None, smtp_recipient=None):
    ''' pull together all the necessary details and send email report '''
    smtp_server = get_smtp_server()
    smtp_sender = get_smtp_sender()
    if smtp_subject is None:
        smtp_subject = get_smtp_subject()
    if smtp_recipient is None:
        smtp_recipient = get_smtp_recipient()
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

def get_config_value(key, default):
    ''' look up key in ansible.cfg '''
    config = AC.load_config_file()
    return AC.get_config(config, 'ansiblereport', key, None, default)

def get_smtp_server():
    ''' look up smtp_server in ansible.cfg '''
    return get_config_value('smtp.server', C.DEFAULT_SMTP_SERVER)

def get_smtp_subject():
    ''' look up smtp_subject in ansible.cfg '''
    return get_config_value('smtp.subject', C.DEFAULT_SMTP_SUBJECT)

def get_smtp_sender():
    ''' look up smtp_sender in ansible.cfg '''
    return get_config_value('smtp.sender', C.DEFAULT_SMTP_SENDER)

def get_smtp_recipient():
    ''' look up smtp_recipient in ansible.cfg '''
    return get_config_value('smtp.recipient', C.DEFAULT_SMTP_RECIPIENT)

def parse_datetime_string(arg):
    ''' take string argument and convert to datetime object '''
    try:
        date = dateutil.parser.parse(arg, default=True)
    except ValueError:
        parts = arg.split()
        if len(parts) != 3 and parts[2] != 'ago':
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
