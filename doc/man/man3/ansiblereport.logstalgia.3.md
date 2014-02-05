ANSIBLEREPORT.LOGSTALGIA(3)
===========================

NAME
----
logstalgia - Logstalgia output plugin for visualization

SYNOPSIS
--------
ansible-report -o logstalgia [options]

DESCRIPTION
-----------

This will query the *ansible-report* database with the provided criteria
and then pipe that into Logstalgia (http://code.google.com/p/logstalgia/) 
for visualization.  You must have Logstalgia already installed.  You can
provide extra arguments to Logstalgia if needed.

OPTIONS
-------

*-e* logstalgia_opts=options, *--extra-args* logstalgia_opts=options

Provide additional options to Logstalgia when rendering the video.  One
example would be:

    -e logstalgia_opts='-1280x720 --output-ppm-stream logs.ppm'

This would allow you to post-process the PPM file with something like
ffmpeg.  More details on recording videos can be found at:

    http://code.google.com/p/logstalgia/wiki/Videos    

COPYRIGHT
---------

Copyright, 2014, University of Oregon

*ansible-report* is released under the terms of the GPLv3 License.
