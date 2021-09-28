#!/usr/bin/env python
# reportpower.py
# This script prints various information from a PiJuice module.
# Copyright 2015-2021 matt.breit@gmail.com
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import io
import sys
import time

from pijuice import (PiJuice, pijuice_hard_functions, pijuice_sys_functions, pijuice_user_functions)

pijuice = PiJuice(1, 0x14)

def fw_version():
   data = 'todo'
   return data

def boot_version():
   data = 'todo'
   return data

def pcb_version():
   data = 'todo'
   return data

def usb_power():
   status = pijuice.status.GetStatus()
   data = status['data']['powerInput5vIo']
   return data

def bat_version():
   data = 'todo'
   return data

def bat_charging():
   status = pijuice.status.GetStatus()
   data = status['data']['battery']
   return data

def bat_percentage():
   chg = pijuice.status.GetChargeLevel()
   data = chg['data']
   return data

def rpi_level():
   vrpi = pijuice.status.GetIoVoltage()
   data = vrpi['data']
   return data

def pico_temp():
   temp = pijuice.status.GetBatteryTemperature()
   data = temp['data']
   return data
def bat_runtime():
   data = 'todo'
   return data

def bat_level():
   vbat = pijuice.status.GetBatteryVoltage()
   data = vbat['data']
   return data


print 'RPI USB Power    : ', usb_power()
print 'Charging Status  : ', bat_charging()
print 'Battery Level    : ', bat_percentage(), '%'
print 'Battery Voltage  : ', bat_level(), 'mV'
print 'RPI Voltage      : ', rpi_level(), 'mV'
print 'UPS Temperature  : ', pico_temp(), 'C'


