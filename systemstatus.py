#!/usr/bin/env python
# -*- coding: utf-8 -*-
### BEGIN LICENSE
#Copyright (c) 2014 Jim Kemp <kemp.jim@gmail.com>

#Permission is hereby granted, free of charge, to any person
#obtaining a copy of this software and associated documentation
#files (the "Software"), to deal in the Software without
#restriction, including without limitation the rights to use,
#copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the
#Software is furnished to do so, subject to the following
#conditions:

#The above copyright notice and this permission notice shall be
#included in all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#OTHER DEALINGS IN THE SOFTWARE.
### END LICENSE

# """ Fetches weather reports Weather.com for display on small screens."""

###############################################################################
#   Raspberry Pi Weather Display
#	By: Jim Kemp	10/25/2014
###############################################################################
#============================================================================================

###############################################################################
#   Raspberry Pi System Status Display
#	By: Matthew Breit 22 Feb 2017
#	Based on "Raspberry Pi Weather Display" by Jim Kemp
#	
###############################################################################

__version__ = "17.2-26"

import os
import pygame
import time
import datetime
from pygame.locals import *
import pywapi
import string
import socket
import fcntl
import struct
from urllib2 import urlopen
import pygame as pg
import signal
import sys
import smbus
import subprocess
import exceptions

# engage the i2c bus for reading from the Pico UPS HV3.0 (firmware 0x24) HAT
i2c = smbus.SMBus(1)

# set environment variable to the PiTFT 2.8" screen attached
os.environ["SDL_FBDEV"] = "/dev/fb1"

# Functions to check the status of various things
def fw_version():
   time.sleep(0.1)
   data = i2c.read_byte_data(0x69, 0x26)
   data = format(data,"02x")
   return data

def boot_version():
   time.sleep(0.1)
   data = i2c.read_byte_data(0x69, 0x25)
   data = format(data,"02x")
   return data

def pcb_version():
   time.sleep(0.1)
   data = i2c.read_byte_data(0x69, 0x24)
   data = format(data,"02x")
   return data

def pwr_mode():
   data = i2c.read_byte_data(0x69, 0x00)
   data = data & ~(1 << 7)
   if (data == 1):
      return "MAIN POWERED"
   elif (data == 2):
      return "BAT POWERED"
   else:
      return "ERROR"

def bat_version():
   time.sleep(0.1)
   data = i2c.read_byte_data(0x6b, 0x07)
   if (data == 0x46):
      return "LiFePO4 (ASCII : F)"
   elif (data == 0x51):
      return "LiFePO4 (ASCII : Q)"
   elif (data == 0x53):
      return "LiPO (ASCII: S)"
   elif (data == 0x50):
      return "LiPO (ASCII: P)"
   else:
      return "ERROR"

def bat_charging():
   time.sleep(0.1)
   data = i2c.read_byte_data(0x69, 0x20)
   if (data == 0x01):
      return "CHARGING"
   if (data == 0x00):
      return "NOT CHARGING"

# how long after power loss before FSSD
def bat_runtime():
   time.sleep(0.1)
   data = i2c.read_byte_data(0x6b, 0x01) + 1
   if (data == 0x100):
      return "TIMER DISABLED"
   elif (data == 0xff):
      return "TIMER DISABLED"
   else:
      data = str(data)+ " MIN"
      return data

# voltage level of battery
def bat_level():
   time.sleep(0.1)
   data = i2c.read_word_data(0x69, 0x08)
   data = format(data,"02x")
   return (float(data) / 100)

# percentage of battery left
def bat_percentage():
   time.sleep(0.1)
   datavolts = bat_level()
   databattery = bat_version()
   if (databattery == "LiFePO4 (ASCII : F)") or (databattery == "LiFePO4 (ASCII : Q)"):
      datapercentage = ((datavolts-2.9)/1.25)*100
   elif (databattery == "LiPO (ASCII: S)") or (databattery == "LiPO (ASCII: P)"):
      datapercentage = ((datavolts-3.4)/(4.4-3.4))*100 # 0% is Pico cutoff of 3.4V, 100% is by testing, 4.26V (edit 3/30/17: now using 4.4V after0x31 firmware update)
   return int(datapercentage)

# voltage level of rpi (from gpio pins)
def rpi_level():
   time.sleep(0.1)
   data = i2c.read_word_data(0x69, 0x0a)
   data = format(data,"02x")
   return (float(data) / 100)

# get a timestamp from the pico rtc
def pico_rtc():
   time.sleep(0.1)
   year = i2c.read_byte_data(0x6a, 0x06)
   year = format(year,"02x")
   month = i2c.read_byte_data(0x6a, 0x05)
   month = format(month,"02x")
   day = i2c.read_byte_data(0x6a, 0x04)
   day = format(day,"02x")
   hour = i2c.read_byte_data(0x6a, 0x02)
   hour = format(hour,"02x")
   min = i2c.read_byte_data(0x6a, 0x01)
   min = format(min, "02x")
   sec = i2c.read_byte_data(0x6a, 0x00)
   sec = format(sec, "02x")
   timestamp = str(year) + "." + str(month) + "." + str(day) + "." + str(hour) + ":" + str(min) + ":" + str(sec)
   return timestamp

# temperature of Pico board (not the fan)
def pico_temp():
   time.sleep(0.1)
   data = i2c.read_byte_data(0x69,0x1b)
   data = format(data,"02x")
   return data

# Get the current SSID that we are connected to, if any.
def get_ssid():
   ssid = subprocess.check_output(["iwgetid","-r"])
   ssid = ssid[0:-1] 
   return ssid

# Get the current temperature of the cpu
def get_cputemp():
   temp = subprocess.check_output(["/opt/vc/bin/vcgencmd"," measure_temp"])
   temp = temp[5:-3]
   return temp

# Get the ip address of the specified adapter
def get_ip_address(ifname):
   try:
   	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    	return ifname +": "+ socket.inet_ntoa(fcntl.ioctl(s.fileno(),	0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15]))[20:24])
   except:
	return ''

# example of application-specific status: I've got another script running in the background which writes a 1 or 0 to a file depending on its state.
def wifiseeker_status():
   try:
        status = subprocess.check_output(["cat","/home/matt/projects/communications/wifiseekerstatus"])
        if (status[0] == '1'):
                return "Active"
        elif (status[0] == '0'):
                return "Idle"
        else:
                return status
   except:
        return "Error"


############################################################################################################
# routine to poll the status getter functions above

def update_status():
	try:
		# Get system statuses
		global startedonbatpower, now, runtime, oldpowermode, startminute, stopminute, timeleft, picortc, ssid, powermode, batlevel, batvolt, rpivolt, charging, picotemp, ipaddress, cputemp
		
                powermode = pwr_mode()

		# prepare a countdown timer for FSSD when the main power is unplugged.
		if (int(runtime) != 256):
			if oldpowermode == 'MAIN POWERED' and powermode == 'BAT POWERED':
				startminute = i2c.read_byte_data(0x6a, 0x01)
				startminute = format(startminute, "02x")
				stopminute = int(startminute) + int(runtime)
			elif oldpowermode == "BAT POWERED" and powermode == "MAIN POWERED":
				stopminute = int(i2c.read_byte_data(0x6a, 0x01)) + int(runtime)
				startedonbatpower = 0
		
			if powermode == 'BAT POWERED' and startedonbatpower == 0:
				now = i2c.read_byte_data(0x6a, 0x01)
				now = format(now, "02x")
				timeleft = stopminute - int(now)
			elif powermode == 'BAT POWERED' and startedonbatpower == 1:
				timeleft = 9999
			else:
				timeleft = int(runtime)
		else:
			timeleft = runtime

		oldpowermode = powermode	
		
		#print "startminute: " + str(int(startminute))
		#print "stopminute : " + str(int(stopminute))
		#print "now        : " + str(int(now))

                batlevel = bat_percentage()
		batvolt = bat_level()
                rpivolt = rpi_level()
                charging = bat_charging()
                picotemp = pico_temp()
		cputemp = get_cputemp()
		picortc = pico_rtc()
		
		# get the ip address of the eth0 and wlan0 interfaces, and display one (preferrably the eth0 one)
                ipaddress = 'n/a'
                ipaddress = get_ip_address('eth0')
                if (ipaddress == ''):
			ipaddress = get_ip_address('wlan0')
			if (ipaddress == ''):
				ipaddress = 'NO IP ADDRESS!'

		# check SSID last, because we might turn off usb bus to save power (in another script), and that might cause these fuctions to throw errors.
		ssid = get_ssid()
		
		return 'true'

	except:
		print "Unexpected error in update_status():", sys.exc_info()[0]
		return 'false'



###############################################################################
# Define the  Display.
class SmDisplay:
	screen = None;
	
	####################################################################
	def __init__(self):
		"Ininitializes a new pygame screen using the framebuffer"
		# Based on "Python GUI in Linux frame buffer"
		# http://www.karoltomala.com/blog/?p=679
		disp_no = os.getenv("DISPLAY")
		#if disp_no:
		#	print "X Display = {0}".format(disp_no)
		
		# Check which frame buffer drivers are available
		# Start with fbcon since directfb hangs with composite output
		drivers = ['fbcon', 'directfb', 'svgalib']
		found = False
		for driver in drivers:
			# Make sure that SDL_VIDEODRIVER is set
			if not os.getenv('SDL_VIDEODRIVER'):
				os.putenv('SDL_VIDEODRIVER', 'fbcon')
			try:
				pygame.display.init()
			except pygame.error:
				print 'Driver: {0} failed.'.format(driver)
				continue
			found = True
			break

		if not found:
			raise Exception('No suitable video driver found!')
		
		size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
		#print "Framebuffer Size: %d x %d" % (size[0], size[1])
		self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
		
		# Clear the screen to start
		self.screen.fill((0, 0, 0))        
		
		# Initialise font support
		pygame.font.init()
		
		# Render the screen
		pygame.mouse.set_visible(0)
		pygame.display.update()
		
		# Calibrate the size of the real display (done by trial and error)
		self.xmax = 320 - 5
		self.ymax = 240 - 5
		
	####################################################################
	def __del__(self):
		"Destructor to make sure pygame shuts down, etc."

	####################################################################
	def disp_status(self):
		try:
			# Fill the screen with black
			self.screen.fill( (0,0,0) )
		
			# setup some boundaries
			xmin = 1
			xmax = self.xmax
			ymax = self.ymax
			lines = 2
		
			# setup some text colors
			lc = (255,255,255)
			lred = (255,0,0)
			lblue = (0,0,255)
			lgreen = (0,255,0)
			lyellow = (255,255,0) 
			lorange = (255,153,0)
		
			# Draw Screen Border
			#pygame.draw.line( self.screen, lc, (xmin,0),(xmax,0), lines )
			#pygame.draw.line( self.screen, lc, (xmin,0),(xmin,ymax), lines )
			#pygame.draw.line( self.screen, lc, (xmin,ymax),(xmax,ymax), lines )
			#pygame.draw.line( self.screen, lc, (xmax,0),(xmax,ymax), lines )
		
			# Display Title
			fn = "monospace" # name
			th = 0.100 # height
			font = pygame.font.SysFont( fn, int(ymax*th), bold=1 )
			txt  = font.render( 'System Status', True, lgreen )
			self.screen.blit( txt, (xmin+10,6) )
		
	 		# Setup Status monitors using smaller font, different location, etc.
			st = 0.16    # Yaxis Start Pos
			gp = 0.065   # Line Spacing Gap
			th = 0.06    # Text Height
			font = pygame.font.SysFont( fn, int(ymax*th), bold=1 )
    
			# Display system Status
			# The ones that help us connect to the system are in orange
			currentdatetime = time.strftime( "%Y.%m.%d.%H:%M.%S", time.localtime() ) # we want the clock to always tick (b/c update_status() is run every minute)
			txt = font.render( currentdatetime, True, lorange )
	                self.screen.blit( txt, (xmin+15,ymax*(st+gp*0)) )

			txt = font.render( ipaddress, True, lorange )
                	self.screen.blit( txt, (xmin+15,ymax*(st+gp*1)) )

			txt = font.render( 'Wifi Network: ' + str(ssid), True, lorange )
			self.screen.blit( txt, (xmin+15,ymax*(st+gp*2)) )
		
			# The rest are in green by default, or other colors depending on status
						
			# power mode
			lpowermode = lgreen
			if (str(powermode) == 'BAT POWERED'):
				lpowermode = lyellow
			txt = font.render( 'Power Mode.......: ' + str(powermode), True, lpowermode )
        	        self.screen.blit( txt, (xmin+15,ymax*(st+gp*3)) )

			txt = font.render( 'Charging Status..: ' + str(charging), True, lgreen )
                        self.screen.blit( txt, (xmin+15,ymax*(st+gp*4)) )

			# Battery Voltage and percentage levels
			lbat = lgreen
			if (str(powermode) == 'BAT POWERED'):
				lbat = lyellow
			if (batvolt < 3.7): # Arbitrary. I get scared at 3.4V :)
				lbat = lred

			txt = font.render( 'Battery level....: ' + str(batlevel) + ' %', True, lbat)
			self.screen.blit( txt, (xmin+15,ymax*(st+gp*5)) )
			
			txt = font.render( 'Battery Voltage..: ' + str(batvolt) + ' V', True, lbat )
                	self.screen.blit( txt, (xmin+15,ymax*(st+gp*6)) )
		
			# RPi System voltage
			txt = font.render( 'System Voltage...: ' + str(rpivolt) + ' V', True, lgreen )
                	self.screen.blit( txt, (xmin+15,ymax*(st+gp*7)) )

			# Temperatures
			txt = font.render( 'PICO Temp........: ' + str(picotemp) + ' C', True, lgreen)
                	self.screen.blit( txt, (xmin+15,ymax*(st+gp*8)) )

			txt = font.render( 'CPU Temp.........: ' + str(cputemp) + ' C', True, lgreen)
			self.screen.blit( txt, (xmin+15,ymax*(st+gp*9)) )
		
			# hardware realtime clock time direct from Pico ups
			txt = font.render( 'PICO RTC Time....: ' + str(picortc), True, lgreen)
			self.screen.blit( txt, (xmin+15,ymax*(st+gp*10)) )
		
			# Time left before file safe shut down if running on battery
			ltimeleft = lgreen
			if (str(powermode) == 'BAT POWERED'):
				ltimeleft = lyellow
			if (timeleft < 5): # arbitrary. I get scared at 5 minutes :)
				ltimeleft = lred
			txt = font.render( 'FSSD Time Left...: ' + str(timeleft) + ' min', True, ltimeleft)
			self.screen.blit( txt, (xmin+15,ymax*(st+gp*11)) )

			# example of checking some application-specific status
			txt = font.render( 'WifiSeeker Status: ' + str(wifiseeker_status()), True, lgreen)
			self.screen.blit( txt, (xmin+15,ymax*(st+gp*12)) )

			# Update the display
			pygame.display.update()
			
			# take a screenshot
			pygame.image.save(self.screen, "screenshot.jpeg")

			return 'true'
		except:
			print "Unexpected error in disp_status(): ", sys.exc_info()[0]
   			return 'false'

############################################################################
# Intercept kill signals (ie during shutdown), and exit gracefully
class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.kill_now = True

############################################################################

killer = GracefulKiller()

# Create an instance of the lcd display class.
myDisp = SmDisplay()

running = True		# Stay running while True
s = 0			# Seconds Placeholder to pace display.
dispTO = 0		# Display timeout to automatically switch back to weather dispaly.

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Main program loop
picortc='n/a'
ssid='n/a'
powermode='n/a'
oldpowermode='n/a'
batlevel=0
batvolt=0
rpivolt=0
charging='n/a'
picotemp=0
ipaddress='n/a'
cputemp=0
runtime = i2c.read_byte_data(0x6b, 0x01) + 1
startminute = i2c.read_byte_data(0x6a, 0x01)
startminute = format(startminute, "02x")
stopminute = int(startminute) + int(runtime)
now = i2c.read_byte_data(0x6a, 0x01)
now = format(now, "02x")

try:
	#pygame.time.wait( 10000 ) # just waiting a few seconds because I run this at boot and would like to see everything else finish before stealing the display
	if pwr_mode() == "BAT POWERED":
		startedonbatpower = 1
	else:
		startedonbatpower = 0

	update_status()
except:
	print "Unexpected error in Main::update_status(): ", sys.exc_info()[0]

while running:
		if (killer.kill_now == True):
			pygame.quit()
			sys.exit()
		
		try:
			if (s != time.localtime().tm_sec):
                		s = time.localtime().tm_sec
				#if (s == 0): # optional. Update the statuses at the top of every minute, or comment to update continuously
				update_status()
		except:
			print  "Unexpected error in Main::whileloop::update_status(): ", sys.exc_info()[0]
		try:
				myDisp.disp_status()
		except:
			print e.strerror
		
		# Loop timer.
		pygame.time.wait( 100 )

pygame.quit()
sys.exit()
