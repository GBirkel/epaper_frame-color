#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# os_setup.py - run a bunch of commands to configure the base Raspberry Pi OS install.
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


def os_setup(wifipassword=""):
    print('Running setup commands...')
    config = read_config()
    if config is None:
        print('Error reading your config.xml file!')
        sys.exit(2)
    print('Read config file.')

    f = codecs.open('/boot/firmware/config.txt', "a", "UTF-8")
    f.write("""
gpio=7=op,dl
gpio=8=op,dl
""")
    f.close()

    run_and_show_command(['wget', 'http://www.airspayce.com/mikem/bcm2835/bcm2835-1.77.tar.gz', '-O', 'bcm2835-1.77.tar.gz'])
    run_and_show_command(['tar', 'xvfz', 'bcm2835-1.77.tar.gz'])
    os.chdir('bcm2835-1.77')
    run_and_show_command(['./configure'])
    run_and_show_command(['make'])
    run_and_show_command(['sudo', 'make', 'install'])
    os.chdir('..')
    run_and_show_command(['rm', '-rf', 'bcm2835-1.77', 'bcm2835-1.77.tar.gz'])

    os.chdir('EPD_13in3e_Utility')
    run_and_show_command(['sudo', 'make', 'clean'])
    run_and_show_command(['sudo', 'make', '-j4'])
    os.chdir('..')

    run_and_show_command(['wget', 'https://cdn.pisugar.com/release/pisugar-power-manager.sh', '-O', '/tmp/pisugar-power-manager.sh'])
    # Unfortunately this command requires user interaction during installation
    #run_and_show_command(['bash', '/tmp/pisugar-power-manager.sh', '-c', 'release'])

    run_and_show_command(['wget', 'https://cdn.pisugar.com/release/PiSugarUpdate.sh', '-O', '/tmp/PiSugarUpdate.sh'])
    #run_and_show_command(['sudo', 'bash', '/tmp/PiSugarUpdate.sh'])

    print('Done.')


def append_to_file(filename, file_as_string):
    f = codecs.open(filename, "a", "UTF-8")
    f.write(file_as_string)
    f.close()


def unregister_service():
    print('Unregistering service...')
    try:
        output = subprocess.check_output('sudo systemctl disable cycle_image.service', shell=True)
    except subprocess.CalledProcessError:
        print("Error disabling service via systemctl!")
        sys.exit(2)
    print('Done.')


if __name__ == "__main__":
    args = argparse.ArgumentParser(description="Run various OS customization commands.")
    args.add_argument('--wifipassword', type=str, default=None, dest='wifipassword',
                      help='Wireless network password', required=False)

    args = args.parse_args()

    os_setup(
        wifipassword=args.wifipassword,
    )
