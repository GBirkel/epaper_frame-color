#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# cycle_image.py - choose an image from the library and send it to the display.
# It is assumed the image is already in grayscale (of whatever bit depth) and the right size.
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

# Set up the service like so:
# sudo ln -s ~/Documents/epaper_frame-color/cycle_image.service /etc/systemd/system/
# sudo systemctl enable cycle_image.service

import argparse, os, re, sys, random, logging
import subprocess
from send_png_to_display import send_png_to_display
from datetime import *
from common_utils import *
from image_database import *
from pisugar_battery import PiSugarBattery


def cycle_image(verbose=False, specific_id=None):

    logger = logging.getLogger("epaper_frame")

    # Instantiate the battery reader and do a first measurement
    piSugarBattery = PiSugarBattery()
    battery_charging_status = piSugarBattery.charging_status()
    if battery_charging_status is not None:
        initial_reading = piSugarBattery.refine_capacity()
        logger.debug("PiSugar 3 battery initial reading: %2i%%." % (initial_reading))

    real_time_clock = piSugarBattery.get_real_time_clock()
    if real_time_clock is None:
        logger.error("Error reading real time clock.")
    else:
        logger.info("PiSugar 3 clock time: %s" % (real_time_clock.isoformat()))

    alarm_setting = piSugarBattery.get_alarm_timer()
    if alarm_setting is None:
        logger.error("Error reading alarm time.")
    else:
        d = datetime.fromtimestamp(alarm_setting, UTC)
        tz_utc = fancytzutc()
        d = d.replace(tzinfo=tz_utc)
        logger.info("PiSugar 3 last alarm time: %s" % (d.isoformat()))

    config = read_config()
    if config is None:
        logger.error('Error reading your config.xml file!')
        sys.exit(2)

    conn = None
    cur = None

    # create a database connection
    database_file = os.path.join(config['installpath'], 'images.db')
    conn = connect_to_local_db(database_file)
    if not conn:
        logger.error("Database could not be opened")
        os._exit(os.EX_IOERR)
    create_tables_if_missing(conn)
    cur = conn.cursor()

    status = get_status_or_defaults(cur, None, None)

    images = get_all_images(cur)
    if verbose:
        logger.info("%s images in library." % (len(images)))
        if status['last_display'] is not None:
            last_display_datetime = datetime.fromtimestamp(status['last_display'], UTC)
            logger.info("Last run at %s." % (pretty_datetime(last_display_datetime)))

    chosen_image = None
    if len(images) > 0:
        chosen_index = random.randint(0, int(len(images) / 2))
        chosen_image = images[chosen_index]

    if verbose:
        logger.info("Chose image %s/%s." % (chosen_image['group_name'], chosen_image['filename']))
        if chosen_image['last_display'] is None:
            logger.info("First time displaying this image.")
        else:
            last_display_datetime = datetime.fromtimestamp(chosen_image['last_display'], UTC)
            logger.info("Display count %s, last displayed %s." % (chosen_image['display_count'], last_display_datetime))

    image_path = os.path.join(config['library'], chosen_image['group_name'], chosen_image['filename'])

    capacity = None
    message = None
    if battery_charging_status is not None:
        capacity = piSugarBattery.refine_capacity()
        message = "%2i%%" % capacity
        if verbose:
            logger.info("PiSugar 3 battery second reading: %2i%%." % (capacity))

    send_png_to_display(verbose, image_path, message)
    report_image_as_displayed(cur, chosen_image['id'], battery_charging_status, capacity)

    current_date = calendar.timegm(datetime.now(UTC).utctimetuple())
    status['last_display'] = current_date
    set_status(cur, status)

    finish_with_database(conn, cur)

    if battery_charging_status is None:
        if verbose:
            logger.warning("PiSugar 3 battery status is undetermined.  Will remain powered on and enable wifi.")
        subprocess.check_call("sudo iwconfig wlan0 txpower on", shell=True, stdout=sys.stdout, stderr=subprocess.STDOUT)

    elif battery_charging_status == True:
        if verbose:
            logger.info("PiSugar 3 battery is charging.  Will remain powered on and enable wifi.")
        subprocess.check_call("sudo iwconfig wlan0 txpower on", shell=True, stdout=sys.stdout, stderr=subprocess.STDOUT)

    else:
        if verbose:
            logger.info("On battery power.  Will disable wifi and power down automatically.")
        subprocess.check_call("sudo iwconfig wlan0 txpower off", shell=True, stdout=sys.stdout, stderr=subprocess.STDOUT)

        if piSugarBattery.set_alarm_for_seconds_from_now(int(config['interval'])) == False:
            logger.error("Failed to set new wakeup time in PiSugar 3!")

        subprocess.check_call("sudo shutdown -P now", shell=True, stdout=sys.stdout, stderr=subprocess.STDOUT)


if __name__ == "__main__":
    args = argparse.ArgumentParser(description="Choose an image from the library and display it")
    args.add_argument("--quiet", "-q", action='store_false', dest='verbose',
                      help="reduce log output")
    args.add_argument('--id', type=str, default=None, dest='specific_id',
                      help='Specific image ID to display', required=False)
    args = args.parse_args()

    set_up_logger()

    cycle_image(
        verbose=args.verbose,
        specific_id=args.specific_id,
    )
