#!/usr/bin/python

import logging
import os.path
import sys

import glob
import os

from subprocess import PIPE
import subprocess
import shlex

from datetime import datetime
now = datetime.now()

sys.path.append(os.path.dirname('/usr/lib/python2.7/site-packages/motioneye/'))
conf_path_given = [False]
run_path_given = [False]
log_path_given = [False]
media_path_given = [False]

import settings

# Execute a shell command
def execute_command(cmd):
    cmdargs = shlex.split(cmd)
    p = subprocess.Popen(cmdargs, stdout=PIPE, stderr=PIPE)
    output, errors = p.communicate()
    if p.returncode:
        print('Failed running %s' % cmd)
        raise Exception(errors)
    return output.decode('utf-8')

# Parse file configuration
def parse_conf_line(line):
        line = line.strip()
        if not line or line.startswith('#'):
            return

        parts = line.split(' ', 1)
        if len(parts) != 2:
            raise Exception('invalid configuration line: %s' % line)

        name, value = parts
        upper_name = name.upper().replace('-', '_')

        if hasattr(settings, upper_name) or 'ADDONS_' in upper_name:
            if 'ADDONS_' not in upper_name:

                curr_value = getattr(settings, upper_name)

                if upper_name == 'LOG_LEVEL':
                    if value == 'quiet':
                        value = 100

                    else:
                        value = getattr(logging, value.upper(), logging.DEBUG)

                elif value.lower() == 'true':
                    value = True

                elif value.lower() == 'false':
                    value = False

                elif isinstance(curr_value, int):
                    value = int(value)

                elif isinstance(curr_value, float):
                    value = float(value)

                if upper_name == 'CONF_PATH':
                    conf_path_given[0] = True

                elif upper_name == 'RUN_PATH':
                    run_path_given[0] = True

                elif upper_name == 'LOG_PATH':
                    log_path_given[0] = True

                elif upper_name == 'MEDIA_PATH':
                    media_path_given[0] = True

            setattr(settings, upper_name, value)

        else:
            logging.warn('unknown configuration option: %s' % name)

# Load global configuration
config_file='/data/etc/motioneye.conf'
with open(config_file) as f:
    for line in f:
        parse_conf_line(line)

# Load addons configuration and init sendmail
user_config_file='/data/etc/send_tiling_image.conf'
with open(user_config_file) as f:
    for line in f:
        parse_conf_line(line)
import sendmail

#sendmail.send_mail(settings.ADDONS_SMTP_SERVER, int(settings.ADDONS_SMTP_PORT), settings.ADDONS_SMTP_ACCOUNT, settings.ADDONS_SMTP_PASSWORD, settings.ADDONS_SMTP_TLS == '1',
#settings.ADDONS_SMTP_FROM, [settings.ADDONS_SMTP_TO], subject="mon test", message="mon message", files=[])
    
# Parameters
cameraid = sys.argv[1]
dateid = sys.argv[2]
hourid = sys.argv[3]
tile = '4x4'

# Search the n last files
os.chdir("/data/media/sda1/%s/%s" % (cameraid, dateid))
files = glob.glob("*-*-*.jpg")
nbtiles = int(eval(tile.replace('x','*')))
files = sorted(files)[-nbtiles:]
with open('/tmp/%s_event_files.txt' % cameraid, "wb" ) as fp:
    for filename in files:
        fp.write("%s\n" % filename)
    fp.close()
    
# Tiling the last event
strnow = '%s:%s:%s.%s' % (now.hour, now.minute, now.second, now.microsecond)
tile_filename = "tiling_event_%s.jpg" % strnow
command="montage @/tmp/%s_event_files.txt -geometry +3+3 -tile 4x4 -background black %s" % (cameraid, tile_filename)
execute_command(command)
