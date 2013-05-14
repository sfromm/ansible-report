# Written by Stephen Fromm <sfromm@gmail.com>
# (C) 2013 University of Oregon
#
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

import imp
import glob
import os

class OutputPlugins:
    ''' manager class for ansible-report plugins '''

    def __init__(self, plugin_path):
        ''' Initialize the plugin manager

        plugin_path: a list of paths to look for plugin modules
        '''

        self.plugin_path = plugin_path
        self.plugins = {}
        self._get_plugins()

    def _load_plugin(self, path):
        ''' for a given path, try to load the module '''
        dir_name = os.path.dirname(path)
        name, ext = os.path.splitext(os.path.basename(path))
        if path in self.plugins:
            return
        try:
            (fp, pathname, description) = imp.find_module(name, [dir_name])
            try:
                module = imp.load_module(name, fp, pathname, description)
            finally:
                fp.close()
        except:
            return
        self.plugins[name] = module.OutputModule()

    def _get_plugins(self):
        ''' iterate over plugin_path and load plugins '''
        for dir_name in self.plugin_path:
            for path in glob.glob(os.path.join(dir_name, '*.py')):
                self._load_plugin(path)
