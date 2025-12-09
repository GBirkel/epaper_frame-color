#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# register_service.py - create and register a service that cycles epaper images on boot.
# The configuration in config.xml is used to construct the right paths.
# Garrett Birkel
# Version 0.1
#
# LICENSE
#
# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the author be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.
#
# Copyright (c) 2025 Garrett Birkel


import argparse, os, re, sys, codecs, time
import subprocess
from common_utils import *


service_template = """[Unit]
Description=update e-paper frame (and shut down when not charging)
After=network.target

[Service]
Type=simple
ExitType=main
ExecStart=/usr/bin/sudo /usr/bin/python3 -u COMMAND
WorkingDirectory=INSTALLPATH
StandardOutput=append:LOGPATH
StandardError=append:LOGPATH
User=USER
Restart=no

[Install]
WantedBy=multi-user.target
"""


def write_file(filename, file_as_string):
    f = codecs.open(filename, "w", "UTF-8")
    f.write(file_as_string)


def register_service():
    print('Registering service...')
    config = read_config()
    if config is None:
        print('Error reading your config.xml file!')
        sys.exit(2)
    print('Read config file.')

    status = None
    try:
        output = subprocess.check_output('sudo systemctl is-enabled cycle_image.service', stderr=subprocess.STDOUT, shell=True)
        status = codecs.utf_8_decode(output)[0].strip()
    except subprocess.CalledProcessError:
        pass
    if status == 'enabled':
        print("Service appears to already be registered.  Re-run with '-u' to unregister.")
        sys.exit(2)

    user = None
    try:
        output = subprocess.check_output('whoami', shell=True)
        user = codecs.utf_8_decode(output)[0].strip()
    except subprocess.CalledProcessError:
        print("Error identifying curent user!")
        sys.exit(2)
    print('Current user is %s' % (user))

    command = os.path.join(config['installpath'], 'cycle_image.py')
    logpath = os.path.join(config['installpath'], 'cycle_image.log')

    content = service_template.replace('COMMAND', command)
    content = content.replace('LOGPATH', logpath)
    content = content.replace('USER', user)
    content = content.replace('INSTALLPATH', config['installpath'])

    filename = os.path.join(config['installpath'], 'cycle_image.service')
    f = codecs.open(filename, "w", "UTF-8")
    f.write(content)
    # Fun fact: If you try to 'enable' a service file that's still open for writing,
    # systemctl will erroneously report it as 'masked', sending you down a rabbit hole.
    f.close()
    print('Wrote service file %s' % (filename))

    try:
        output = subprocess.check_output('sudo systemctl link ' + filename, shell=True)
    except subprocess.CalledProcessError:
        print("Error linking service with systemctl!  Try unregistering with '-u' first.")
        sys.exit(2)
    print('Linked service.')

    try:
        output = subprocess.check_output('sudo systemctl enable cycle_image.service', shell=True)
    except subprocess.CalledProcessError:
        print("Error enabling service with systemctl!")
        sys.exit(2)
    print('Enabled service.')

    print('Done.')


def unregister_service():
    print('Unregistering service...')
    try:
        output = subprocess.check_output('sudo systemctl disable cycle_image.service', shell=True)
    except subprocess.CalledProcessError:
        print("Error disabling service via systemctl!")
        sys.exit(2)
    print('Done.')


if __name__ == "__main__":
    args = argparse.ArgumentParser(description="Register the image cycler as a system service.")
    args.add_argument("--unregister", "-u", action='store_true', dest='unregister',
                      help="unregister the service")
    args = args.parse_args()

    if args.unregister:
        unregister_service()
    else:
        register_service()
