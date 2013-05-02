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

def format_task_brief(task):
    ''' summarize a task into a brief string '''
    return "{0} {1} {2}: {3}".format(
            task.timestamp.strftime(C.DEFAULT_SHORT_STRFTIME),
            task.hostname,
            task.module, task.result)

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
        report += '\n  {0:-^25}\n\n'.format(' Tasks ')
        for task in pb['tasks']:
            report += "  {0}\n".format(task[0])

        report += '\n  {0:-^25}\n\n'.format(' Summary ')
        for host, stats in pb['stats'].items():
            summary = ''
            if 'ok' in stats:
                summary += "{0}={1}  ".format('ok', stats['ok'])
            for stat in sorted(stats.keys()):
                if stat == 'ok':
                    continue
                summary += "{0}={1}  ".format(stat.lower(), stats[stat])
            report += "  {0}\t: {1}\n".format(host, summary)
            report += "\n\n\n"
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
