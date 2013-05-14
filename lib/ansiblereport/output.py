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

class OutputModule:
    ''' 
    A generic plugin that all output plugins should implement
    for ansible-report to recognize them.  It should implement the 
    following:

    name        Attribute with the name of the plugin
    do_report   Method that will take a list of events and report
                them in some manner.  It also takes an optional 
                set of keyword arguments
    '''
    name = 'generic'

    def do_report(self, events, **kwargs):
        ''' take list of events and do something with them '''
        pass
