#!/usr/bin/python

import logging
import os.path
import shutil
import sys

import glob
import os

from subprocess import PIPE
import subprocess
import shlex

import time
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
        print('Failed running %(cmd)s' % locals())
        raise Exception(errors)
    return output.decode('utf-8')

# Parse file configuration
def parse_conf_line(line):
        line = line.strip()
        if not line or line.startswith('#'):
            return

        parts = line.split(' ', 1)
        if len(parts) != 2:
            raise Exception('invalid configuration line: %(line)s' % locals())

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
            logging.warn('unknown configuration option: %(name)s' % locals())

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

   
# Parameters
camera_id = sys.argv[1]
date_id = sys.argv[2]
hour_id = sys.argv[3]
tile = '4x4'

# Wait time span (actualy, not from global preference)
# Must use IOLoop ?
time.sleep(int(settings.ADDONS_TIMESPAN))

# Search the n last files
camera_folder = "/data/media/sda1/%(camera_id)s" % locals()
os.chdir("%(camera_folder)s/%(date_id)s" % locals())
files = glob.glob("*-*-*.jpg")
nbtiles = int(eval(settings.ADDONS_TILE.replace('x','*')))
files = sorted(files)[-nbtiles:]
with open('/tmp/%(camera_id)s_event_files.txt' % locals(), "wb" ) as fp:
    for filename in files:
        fp.write("%(filename)s\n" % locals())
    fp.close()
    
# Create folders if not exist
tile_folder =  "%(camera_folder)s/%(date_id)s/tiling" % locals()
if not os.path.isdir(tile_folder):
    os.mkdir(tile_folder)

# Create folders if not exist
lastsnap_folder = "%(camera_folder)s/tiling" % locals()
if not os.path.isdir(lastsnap_folder):
    os.mkdir(lastsnap_folder)

# Tiling the last event
strnow = '%02d-%02d-%02d' % (now.hour, now.minute, now.second)
tile_filename = "%(tile_folder)s/%(strnow)s.jpg" % locals()
img_quality='50'
command="montage @/tmp/%(camera_id)s_event_files.txt -geometry +3+3 -tile 4x4 -strip -quality %(img_quality)s -background black %(tile_filename)s" % locals()
execute_command(command)

# Create symbolic link
target = "%(lastsnap_folder)s/lastsnap.jpg" % locals()
if os.path.isfile(tile_filename):
    #Symbolic link seems not working by ftp server
    #os.symlink(tile_filename,target)
    shutil.copy(tile_filename, target)

# Send email
sendmail.send_mail(settings.ADDONS_SMTP_SERVER, int(settings.ADDONS_SMTP_PORT), settings.ADDONS_SMTP_ACCOUNT, settings.ADDONS_SMTP_PASSWORD, settings.ADDONS_SMTP_TLS == '1',
settings.ADDONS_SMTP_FROM, [settings.ADDONS_SMTP_TO], subject="Camera event on %(camera_id)s" % locals(), message="Camera event on %(camera_id)s" % locals(), files=[tile_filename])
