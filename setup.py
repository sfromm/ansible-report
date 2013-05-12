#!/usr/bin/env python

import os
import sys

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

from ansiblereport import __version__, __author__, __name__
from distutils.core import setup

PLUGIN_PATH = 'share/ansible_plugins/callback_plugins'

setup(name=__name__,
      version=__version__,
      author=__author__,
      author_email='sfromm@gmail.com',
      url='https://github.com/sfromm/ansible-report',
      description='Utility to log and report ansible activity',
      license='GPLv3',
      package_dir={ 'ansiblereport': 'lib/ansiblereport' },
      packages=['ansiblereport'],
      scripts=['bin/ansible-report'],
      data_files=[(PLUGIN_PATH, ['plugins/callback_plugins/ansiblereport-logger.py'])],
      install_requires=['SQLAlchemy>=0.6', 'alembic', 'dateutil'],
)
