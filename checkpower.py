#!/usr/bin/env python
# checkpower.py
# this script runs on boot and checks the USB power connection on boot and periodically.
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


# If USB power is detected, run as normal.
# If USB power is not detected, initiate standby protocol.
# If USB power is lost, initiate standby protocol.
# If USB power is reconnected, cancel standby protocol.
# Check for USB power every minute.
# Standby protocol should be:
# 1. Run for 5 minutes
# 2. If still no USB Power, program the PiJuice to wake every hour, and shutdown.

import os
import io
import sys
import time
from pijuice import (PiJuice, pijuice_hard_functions, pijuice_sys_functions, pijuice_user_functions)
import StringIO
import ConfigParser

# load configuation (email addresses, etc. from a simple config.txt file)
# our config file in this case doesn't have a header (because we also use it for bash scripts).
# so we add the header by bringing the config file in as a string.
dummy = StringIO.StringIO()
dummy.write('[TOP]\n')
dummy.write(open('/home/matt/projects/config.txt').read())
dummy.seek(0, os.SEEK_SET)
config = ConfigParser.ConfigParser()
config.readfp(dummy)
email_address_phone = config.get('TOP','EMAIL_ADD_TO_PHONE')

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

# Set RTC alarm clock
# on the 0 second of the 0 minute of every hour of every day of every month of every year, wakeup.
def set_rtcAlarm(schedule):
	try:
		status = pijuice.rtcAlarm.SetAlarm(schedule)

		if status['error'] != 'NO_ERROR':
			return('Cannot set alarm: ' + str(status['error']))
		else:
    			return ('Wakeup set for ' + str(pijuice.rtcAlarm.GetAlarm()))
	except:
		return 'set_rtcAlarm() Exception!'
# ==============================================================================

print usb_power()
print bat_charging()
print bat_percentage()
print bat_level()
print rpi_level()
print pico_temp()

# intialize alarm
a={}
a['year'] = 'EVERY_YEAR'
a['month'] = 'EVERY_MONTH'
a['day'] = 'EVERY_DAY'
a['hour'] = 'EVERY_HOUR'
a['minute'] = 0
a['second'] = 0

# print set_rtcAlarm(a) # for debugging

# optional: set to true to always wake up the pi periodically no matter how it is shut down
pijuice.rtcAlarm.SetWakeupEnabled(False)

standbyRunTime = 300 # seconds
minBatForWakeup = 1 # if Battery is below this level, Rpi will not wake up again.
loopRunning = True

while loopRunning == True:
	usbPowerState = usb_power()

	# USB Power is Present
	if (usbPowerState == 'PRESENT'):
		print 'USB Power is connected'
		
	# USB Power is not Present
	elif (usbPowerState == 'NOT_PRESENT'):
		print 'USB power is NOT connected. Initiating Standby Protocol...'
		
		time.sleep(standbyRunTime)
		
		# check USB power one more time before shutting down
		if (usb_power() == 'NOT_PRESENT'):
			loopRunning = False
			print 'Shutting down!'
			
			if (bat_percentage() >= minBatForWakeup):
				set_rtcAlarm(a)
				pijuice.rtcAlarm.SetWakeupEnabled(True)
				print 'Wakeup is now enabled.'
				command = "sudo ./systemmailer.sh custom SHTDWN:BAT_"
			else:
				pijuice.rtcAlarm.SetWakeupEnabled(False)
				print 'Battery is too low. Wakeup disabled.'
				command = "sudo ./systemmailer.sh custom SHTDWN_FINAL:BAT_"

			pijuice.power.SetPowerOff(60) # shut Pijuice down 60 seconds after shutdown
			command = command + str(bat_percentage())
			command = command + "%"
			command = command + email_address_phone
			os.system(command)
        		os.system("shutdown -h now")
		else:
			print 'USB power restored! Standby Protocol cancelled!'
	
	# USB Power is weak or bad
	else:
		print 'USB Power is connected, but is not ideal: ', usbPowerState
 
	time.sleep(60)
