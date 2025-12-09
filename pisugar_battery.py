#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# pisugar_utils.py - code to read the status of the PiSugar 3 from the bus.
# Based on https://github.com/nullm0ose/pwnagotchi-plugin-pisugar3 .
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
import struct
from datetime import *


PiSugar3_Addr = 0x57

# Parse a hexadecimal value mocked to look a decimal into the actual decimal value.
# e.g. 0x36 becomes 36, not 54.
def hexAsDec(v):
    if v is None: return None
    return int((v & 0x0F) + (((v & 0xF0) / 16) * 10))

# Express a decimal value in hexadecimal that looks like the visual equivalent.
# e.g. 54 becomes 0x54, not 0x36.
def decAsHex(v):
    if v is None: return None
    return (int(v / 10) * 16) + (v % 10)


class PiSugarBattery:

    def __init__(self):
        import smbus
        self._bus = smbus.SMBus(1)
        self.sample_size = 25
        self.battery_readings = []


    def capacity(self):
        battery_level = 0
        try:
            battery_level = self._bus.read_byte_data(PiSugar3_Addr, 0x2a)
        except:
            pass
        return battery_level


    # Returns the current alarm timer setting, expressed in seconds
    # starting from midnight (12:00am).
    def get_real_time_clock(self):
        try:
            yrRaw = self._bus.read_byte_data(PiSugar3_Addr, 0x31)
            mon = self._bus.read_byte_data(PiSugar3_Addr, 0x32)
            dayRaw = self._bus.read_byte_data(PiSugar3_Addr, 0x33)
            h = self._bus.read_byte_data(PiSugar3_Addr, 0x35)
            minRaw = self._bus.read_byte_data(PiSugar3_Addr, 0x36)
            secRaw = self._bus.read_byte_data(PiSugar3_Addr, 0x37)
        except:
            return None
        clock_as_datetime = None
        try:
            # These are hexadecimal values mocked to look like decimals,
            # e.g. 0x36 is actually 36 minutes, not 54 minutes.
            yr = hexAsDec(yrRaw)
            day = hexAsDec(dayRaw)
            min = hexAsDec(minRaw)
            sec = hexAsDec(secRaw)
            clock_as_datetime = datetime(yr + 2000, mon, day, hour=h, minute=min, second=sec, tzinfo=timezone.utc)
        except ValueError:
            return None
        return clock_as_datetime


    # Returns the current alarm timer setting, expressed in seconds
    # starting from midnight (12:00am).
    def get_alarm_timer(self):
        try:
            hourRaw = self._bus.read_byte_data(PiSugar3_Addr, 0x45)
            minRaw = self._bus.read_byte_data(PiSugar3_Addr, 0x46)
            secRaw = self._bus.read_byte_data(PiSugar3_Addr, 0x47)
        except:
            return None
        hour = hexAsDec(hourRaw)
        min = hexAsDec(minRaw)
        sec = hexAsDec(secRaw)
        return (((hour * 60) + min) * 60) + sec


    # Sets the alarm timer setting, with the given h=hours, m=minutes, s=seconds
    # but does not check to see if the timer is actually enabled.
    def set_alarm_timer(self, hour, min, sec):

        hourHex = decAsHex(hour)
        minHex = decAsHex(min)
        secHex = decAsHex(sec)
        try:
            # Turn off write protection
            self._bus.write_byte_data(PiSugar3_Addr, 0x0B, 0x29)
            # Write in the new time
            self._bus.write_byte_data(PiSugar3_Addr, 0x45, hourHex)
            self._bus.write_byte_data(PiSugar3_Addr, 0x46, minHex)
            self._bus.write_byte_data(PiSugar3_Addr, 0x47, secHex)
            # Turn on write protection
            self._bus.write_byte_data(PiSugar3_Addr, 0x0B, 0xFF)
        except:
            return False
        return True


    # Sets the alarm timer for the given seconds after the current time
    # (as read from the real time clock)
    def set_alarm_for_seconds_from_now(self, seconds_later):
        # Read out the current hours, minutes, and seconds time
        try:
            hourRaw = self._bus.read_byte_data(PiSugar3_Addr, 0x35)
            minRaw = self._bus.read_byte_data(PiSugar3_Addr, 0x36)
            secRaw = self._bus.read_byte_data(PiSugar3_Addr, 0x37)
        except:
            return False
        hour = hexAsDec(hourRaw)
        min = hexAsDec(minRaw)
        sec = hexAsDec(secRaw)
        current_total_seconds = (((hour*60) + min) * 60) + sec
        target_total_seconds = (current_total_seconds + seconds_later) % (60 * 60 * 24) # Confine to 24 hours
        newHour = int(target_total_seconds / (60*60))
        newMin = int(target_total_seconds / 60) - (newHour*60)
        newSec = target_total_seconds % 60
        return self.set_alarm_timer(newHour, newMin, newSec)


    def charging_status(self):
        # Try to read the bus, if it fails, return None.
        try:
            stat02 = self._bus.read_byte_data(PiSugar3_Addr, 0x02)
        except:
            return None
        if stat02 == None:
            return None
        if stat02 & 0x80:
            return True
        return False


    def refine_capacity(self):
        if len(self.battery_readings) >= self.sample_size:
            self.battery_readings.pop(0)
        self.battery_readings.append(self.capacity())

        return int(sum(self.battery_readings) / len(self.battery_readings))


if __name__ == "__main__":

    import time
    from common_utils import fancytzutc

    # Instantiate the battery reader and do a first measurement
    piSugarBattery = PiSugarBattery()
    battery_charging_status = piSugarBattery.charging_status()
    if battery_charging_status is not None:
        initial_reading = piSugarBattery.refine_capacity()
        print("PiSugar 3 battery initial reading: %2i%%." % (initial_reading))

    real_time_clock = piSugarBattery.get_real_time_clock()
    if real_time_clock is None:
        print("Error reading real time clock.")
    else:
        print(real_time_clock.isoformat())

    alarm_setting = piSugarBattery.get_alarm_timer()
    if alarm_setting is None:
        print("Error reading alarm time.")
    else:
        d = datetime.fromtimestamp(alarm_setting, UTC)
        tz_utc = fancytzutc()
        d = d.replace(tzinfo=tz_utc)
        print(d.isoformat())

        formatted = f'{d:%I}:{d:%M}:{d:%S} {d:%p}'
        print("Alarm time: %s seconds, or %s." % (alarm_setting, formatted))

    #piSugarBattery.set_alarm_for_seconds_from_now(180)


