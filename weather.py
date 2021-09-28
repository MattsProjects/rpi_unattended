#!/usr/bin/env python
# -*- coding: utf-8 -*-
# weather.py
# This is the example unattended application which displays weather, radar, and system status.
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
#
#Copyright (c) 2014 Jim Kemp <kemp.jim@gmail.com>
#
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

""" Fetches weather reports Weather.com for display on small screens."""

__version__ = "0.0.8"

###############################################################################
#   Raspberry Pi Weather Display
#	By: Jim Kemp	10/25/2014
###############################################################################
import os
import pygame
import time
import datetime
import random
from pygame.locals import *
import calendar
import serial

import pywapi
import weathercom
#from pyowm import OWM
#from pyowm.utils import config
#from pyowm.utils import timestamps
import string

#owm = OWM('0cece166d95123818d73cc67d5d756e0')
#mgr = owm.weather_manager()

from icon_defs import *

import socket
import fcntl
import struct

from urllib2 import urlopen
import io
import pygame as pg
import signal
import sys
import smbus
import subprocess

from pijuice import (PiJuice, pijuice_hard_functions, pijuice_sys_functions, pijuice_user_functions)

pijuice = PiJuice(1, 0x14)

i2c = smbus.SMBus(1)

os.environ["SDL_FBDEV"] = "/dev/fb1"

def fw_version():
   data = 'todo'
   return data

def boot_version():
   data = 'todo'
   return data

def pcb_version():
   data = 'todo'
   return data

def pwr_mode():
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

def bat_runtime():
   data = 'todo'
   return data

def bat_level():
   vbat = pijuice.status.GetBatteryVoltage()
   data = vbat['data']
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

###############################################################################
#get ip address
def get_ip_address(ifname):
    	try:
    		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    		return ifname +": "+ socket.inet_ntoa(fcntl.ioctl(s.fileno(),	0x8915,  # SIOCGIFADDR
        		struct.pack('256s', ifname[:15]))[20:24])
    	except:
		return ''

def check_internet():
	 return 0 
	# return os.system("ping -c 1 google.com > /dev/null 2>&1") # Causes display freeze...
	
###############################################################################
def getIcon( w, i ):
	try:
		return int(w['forecasts'][i]['day']['icon'])
	except:
		return 29

# Small LCD Display.
class SmDisplay:
	screen = None;
	
	####################################################################
	def __init__(self):
		"Ininitializes a new pygame screen using the framebuffer"
		# Based on "Python GUI in Linux frame buffer"
		# http://www.karoltomala.com/blog/?p=679
		disp_no = os.getenv("DISPLAY")
		if disp_no:
			print "X Display = {0}".format(disp_no)
		
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
		print "Framebuffer Size: %d x %d" % (size[0], size[1])
		self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
		# Clear the screen to start
		self.screen.fill((0, 0, 0))        
		# Initialise font support
		pygame.font.init()
		# Render the screen
		pygame.mouse.set_visible(0)
		pygame.display.update()
		#for fontname in pygame.font.get_fonts():
		#        print fontname
		self.temp = '??'
		self.feels_like = 0
		self.wind_speed = 0
		self.baro = 0.0
		self.wind_dir = 'S'
		self.humid = 0
		self.wLastUpdate = ''
		self.day = [ '', '', '', '' ]
		self.icon = [ 0, 0, 0, 0 ]
		self.rain = [ '', '', '', '' ]
		self.temps = [ ['',''], ['',''], ['',''], ['',''] ]
		self.sunrise = '7:00 AM'
		self.sunset = '8:00 PM'
		self.text = 'default'

		# Display
		self.xmax = 320 - 5
		self.ymax = 240 - 5
		self.scaleIcon = True		# Weather icons need scaling.
		self.iconScale = 0.25		# Icon scale amount.
		self.subwinTh = 0.05		# Sub window text height
		self.tmdateTh = 0.100		# Time & Date Text Height
		self.tmdateSmTh = 0.06
		self.tmdateYPos = 6		# Time & Date Y Position
		self.tmdateYPosSm = 14		# Time & Date Y Position Small

		# connection
		self.internet = 0
		self.ipaddresseth0 = '0.0.0.0'
		self.ipaddresswlan0 = '0.0.0.0'
	####################################################################
	def __del__(self):
		"Destructor to make sure pygame shuts down, etc."

	####################################################################
	def UpdateWeather(self):
		print "0"
		# Use Weather.com for source data.
		cc = 'current_conditions'
		print "0c"
		f = 'forecasts'
		print "0b"
		# This is where the magic happens. 
		try:
			self.ipaddresseth0 = get_ip_address('eth0')
			self.ipaddresswlan0 = get_ip_address('wlan0')
			print "0d"
			if (check_internet() == 0):
				print "0e"
				#self.w = pywapi.get_weather_from_noaa('19390')
				self.w = weathercom.getCityWeatherDetails(city="19390")
				#observation = mgr.weather_at_place('19390')
				#x = observation.weather
				print "1"
				print self.w
				w = self.w
				#if ( w[cc]['last_updated'] != self.wLastUpdate ): #todo: can i force an update if temp = ??
				self.wLastUpdate = w[cc]['last_updated']
				print "New Weather Update: " + self.wLastUpdate
				self.text = string.lower( w[cc]['text'])
				self.temp = w.temperature('fahrenheit')
				self.temp = string.lower( w[cc]['temperature'] )
				self.feels_like = string.lower( w[cc]['feels_like'] )
				self.wind_speed = string.lower( w[cc]['wind']['speed'] )
				self.baro = string.lower( w[cc]['barometer']['reading'] )
				self.wind_dir = string.upper( w[cc]['wind']['text'] )
				self.humid = string.upper( w[cc]['humidity'] )
				self.vis = string.upper( w[cc]['visibility'] )
				self.gust = string.upper( w[cc]['wind']['gust'] )
				self.wind_direction = string.upper( w[cc]['wind']['direction'] )
				self.day[0] = w[f][0]['day_of_week']
				self.day[1] = w[f][1]['day_of_week']
				self.day[2] = w[f][2]['day_of_week']
				self.day[3] = w[f][3]['day_of_week']
				self.sunrise = w[f][0]['sunrise']
				self.sunset = w[f][0]['sunset']
				self.icon[0] = getIcon( w, 0 )
				self.icon[1] = getIcon( w, 1 )
				self.icon[2] = getIcon( w, 2 )
				self.icon[3] = getIcon( w, 3 )
				print 'Icon Index: ', self.icon[0], self.icon[1], self.icon[2], self.icon[3]
				print 'File: ', sd+icons[self.icon[0]]
				self.rain[0] = w[f][0]['day']['chance_precip']
				self.rain[1] = w[f][1]['day']['chance_precip']
				self.rain[2] = w[f][2]['day']['chance_precip']
				self.rain[3] = w[f][3]['day']['chance_precip']
				if ( w[f][0]['high'] == 'N/A' ):
					self.temps[0][0] = '--'
				else:	
					self.temps[0][0] = w[f][0]['high'] + unichr(0x2109)
				self.temps[0][1] = w[f][0]['low'] + unichr(0x2109)
				self.temps[1][0] = w[f][1]['high'] + unichr(0x2109)
				self.temps[1][1] = w[f][1]['low'] + unichr(0x2109)
				self.temps[2][0] = w[f][2]['high'] + unichr(0x2109)
				self.temps[2][1] = w[f][2]['low'] + unichr(0x2109)
				self.temps[3][0] = w[f][3]['high'] + unichr(0x2109)
				self.temps[3][1] = w[f][3]['low'] + unichr(0x2109)
				print "2"
				image_url = 'http://sirocco.accuweather.com/nx_mosaic_640x480_public/sir/inmsirpa_.gif'
                                resource = urlopen(image_url)
                                print "3"
				output = open("radar.jpg","wb")
                                print "4"
				output.write(resource.read())
                                print "5"
				output.close()
				print "radar loaded"
				self.internet = check_internet()
				return True
			else:
				self.text = 'No Internet'
    
		except Exception as err:
			print ("Weather Error {0}".format(err))
			self.temp = '??'
			return False
		
		#return True



	####################################################################
	def disp_weather(self):
		# Fill the screen with black
		self.screen.fill( (0,0,0) )
		xmin = 1
		xmax = self.xmax
		ymax = self.ymax
		lines = 2
		lc = (255,255,255)
		lred = (255,0,0)
		lblue = (0,0,255)
		lgreen = (0,255,0)
		lorange = (255,165,0) 
		fn = "freesans"

		# Draw Screen Border
		pygame.draw.line( self.screen, lc, (xmin,0),(xmax,0), lines )
		pygame.draw.line( self.screen, lc, (xmin,0),(xmin,ymax), lines )
		pygame.draw.line( self.screen, lc, (xmin,ymax),(xmax,ymax), lines )	# Bottom
		pygame.draw.line( self.screen, lc, (xmax,0),(xmax,ymax), lines )
		pygame.draw.line( self.screen, lc, (xmin,ymax*0.15),(xmax,ymax*0.15), lines )
		pygame.draw.line( self.screen, lc, (xmin,ymax*0.5),(xmax,ymax*0.5), lines )
		pygame.draw.line( self.screen, lc, (xmax*0.25,ymax*0.5),(xmax*0.25,ymax), lines )
		pygame.draw.line( self.screen, lc, (xmax*0.5,ymax*0.15),(xmax*0.5,ymax), lines )
		pygame.draw.line( self.screen, lc, (xmax*0.75,ymax*0.5),(xmax*0.75,ymax), lines )

		# Time & Date
		th = self.tmdateTh
		sh = self.tmdateSmTh
		font = pygame.font.SysFont( fn, int(ymax*th), bold=1 )	# Regular Font
		sfont = pygame.font.SysFont( fn, int(ymax*sh), bold=1 )	# Small Font for Seconds

		tm1 = time.strftime( "%a, %b %d   %I:%M:%S %P", time.localtime() )	# 1st part
		#tm2 = time.strftime( "%S", time.localtime() )					# 2nd
		#tm3 = time.strftime( " %P", time.localtime() )					# 

		rtm1 = font.render( tm1, True, lgreen )
		(tx1,ty1) = rtm1.get_size()
		#rtm2 = sfont.render( tm2, True, lgreen )
		#(tx2,ty2) = rtm2.get_size()
		#rtm3 = font.render( tm3, True, lgreen )
		#(tx3,ty3) = rtm3.get_size()

		#tp = xmax / 2 - (tx1 + tx2 + tx3) / 2
		tp = xmax / 2 - tx1 / 2
		self.screen.blit( rtm1, (tp,self.tmdateYPos) )
		#self.screen.blit( rtm2, (tp+tx1+3,self.tmdateYPosSm) )
		#self.screen.blit( rtm3, (tp+tx1+tx2,self.tmdateYPos) )

		# Outside Temp
		font = pygame.font.SysFont( fn, int(ymax*(0.5-0.15)*0.75), bold=1 )
		txt = font.render( self.temp, True, lgreen)
		(tx,ty) = txt.get_size()
		# Show degree F symbol using magic unicode char in a smaller font size.
		dfont = pygame.font.SysFont( fn, int(ymax*(0.5-0.15)*0.5), bold=1 )
		dtxt = dfont.render( unichr(0x2109), True, lgreen )
		(tx2,ty2) = dtxt.get_size()
		# show text of current conditions
		efont = pygame.font.SysFont(fn, int(ymax*(0.5-0.15)*0.17), bold=1)
		etxt = efont.render(self.text, True, lgreen)
		(tx3,ty3) = etxt.get_size()

		x = xmax*0.27 - (tx*1.02 + tx2) / 2
		self.screen.blit( txt, (x,ymax*0.15) )
		x = x + (tx*1.02)
		self.screen.blit( dtxt, (x,ymax*0.2) )
		x = xmax*0.26 - (tx3/2)
		self.screen.blit( etxt, (x,ymax*0.41))
		
		# Conditions
		st = 0.16    # Yaxis Start Pos
		gp = 0.065   # Line Spacing Gap
		th = 0.06    # Text Height
		dh = 0.05    # Degree Symbol Height
		so = 0.01    # Degree Symbol Yaxis Offset
		xp = 0.52    # Xaxis Start Pos
		x2 = 0.78    # Second Column Xaxis Start Pos

		font = pygame.font.SysFont( fn, int(ymax*th), bold=1 )
    
	  	# display ip address
		ipaddress = 'No IP Address!'
		try:
			if (self.ipaddresseth0 != ''):
				ipaddress = self.ipaddresseth0
				internet = self.internet
				if (internet == 0):
      					txt = font.render( ipaddress, True, lgreen )
				elif (internet == 1):
					txt = font.render( ipaddress, True, lorange )
				else:
					txt = font.render( ipaddress, True, lred)
			elif (self.ipaddresswlan0 != ''):
				ipaddress = self.ipaddresswlan0
				internet = self.internet
				if (internet == 0):
      					txt = font.render( ipaddress, True, lgreen )
				elif (internet == 1):
					txt = font.render( ipaddress, True, lorange )
				else:
					txt = font.render( str(internet), True, lred )
    			else:
      				txt = font.render( ipaddress, True, lred )  
		except:
			print "ipaddress error"
			ipaddress = 'Error'
			txt = font.render(ipaddress,True,lred)
			pass

		self.screen.blit( txt, (xmax*xp,ymax*(st+gp*4)) )
		txt = font.render( '', True, lc )
		self.screen.blit( txt, (xmax*x2,ymax*(st+gp*4)) )
		(tx,ty) = txt.get_size()
		# Show degree F symbol using magic unicode char.
		#dfont = pygame.font.SysFont( fn, int(ymax*dh), bold=1 )
		#dtxt = dfont.render( unichr(0x2109), True, lc )
		#self.screen.blit( dtxt, (xmax*x2+tx*1.01,ymax*(st+so)) )

		txt = font.render( 'High: ' + self.temps[0][0],True,lgreen)
		self.screen.blit( txt, (xmax*xp,ymax*(st+gp*0)) )
		
		txt = font.render( 'Low: ' + self.temps[0][1], True, lgreen)
		self.screen.blit( txt, (xmax*x2,ymax*(st+gp*0)) )

		#txt = font.render( 'Wind:', True, lc )
		#self.screen.blit( txt, (xmax*xp,ymax*(st+gp*1)) )
		#txt = font.render( self.wind_speed+' mph', True, lc )
		#self.screen.blit( txt, (xmax*x2,ymax*(st+gp*1)) )

		txt = font.render( 'Wind:', True, lc )
		self.screen.blit( txt, (xmax*xp,ymax*(st+gp*2)) )
		txt = font.render( str(self.wind_speed)+' mph', True, lc )
		self.screen.blit( txt, (xmax*x2,ymax*(st+gp*2)) )

		txt = font.render( 'Windchill:', True, lc )
		self.screen.blit( txt, (xmax*xp,ymax*(st+gp*3)) )
		txt = font.render( str(self.feels_like) +unichr(0x2109), True, lc )
		self.screen.blit( txt, (xmax*x2,ymax*(st+gp*3)) )

		txt = font.render( 'Humidity:', True, lc )
		self.screen.blit( txt, (xmax*xp,ymax*(st+gp*1)) )
		txt = font.render( str(self.humid)+'%', True, lc )
		self.screen.blit( txt, (xmax*x2,ymax*(st+gp*1)) )

		wx = 	0.125			# Sub Window Centers
		wy = 	0.510			# Sub Windows Yaxis Start
		th = 	self.subwinTh		# Text Height
		rpth = 	0.100			# Rain Present Text Height
		gp = 	0.065			# Line Spacing Gap
		ro = 	0.010 * xmax   	# "Rain:" Text Window Offset winthin window. 
		rpl =	5.95			# Rain percent line offset.

		font = pygame.font.SysFont( fn, int(ymax*th), bold=1 )
		rpfont = pygame.font.SysFont( fn, int(ymax*rpth), bold=1 )

		# Sub Window 1
		txt = font.render( self.day[0]+":", True, lgreen )
		(tx,ty) = txt.get_size()
		self.screen.blit( txt, (xmax*wx-tx/2,ymax*(wy+gp*0)) )
		txt = font.render( self.temps[0][0] + ' / ' + self.temps[0][1], True, lgreen)
		(tx,ty) = txt.get_size()
		self.screen.blit( txt, ((xmax*wx-tx/2),(ymax*(wy+gp*5))) )
		rptxt = rpfont.render( self.rain[0]+'%', True, lgreen )
		(tx,ty) = rptxt.get_size()
		self.screen.blit( rptxt, (xmax*wx-tx/2,ymax*(wy+gp*rpl)) )
		icon = pygame.image.load(sd + icons[self.icon[0]]).convert_alpha()
		(ix,iy) = icon.get_size()
		if self.scaleIcon:
			icon2 = pygame.transform.scale( icon, (int(ix*0.5),int(iy*0.5)) )
			(ix,iy) = icon2.get_size()
			icon = icon2
		if ( iy < 90 ):
			yo = (90 - iy) / 2 
		else: 
			yo = 0
		self.screen.blit( icon, (xmax*wx-ix/2,ymax*(wy+gp*1.2)+yo-20) )

		# Sub Window 2
		txt = font.render( self.day[1]+':', True, lc )
		(tx,ty) = txt.get_size()
		self.screen.blit( txt, (xmax*(wx*3)-tx/2,ymax*(wy+gp*0)) )
		txt = font.render( self.temps[1][0] + ' / ' + self.temps[1][1], True, lc )
		(tx,ty) = txt.get_size()
		self.screen.blit( txt, (xmax*wx*3-tx/2,ymax*(wy+gp*5)) )
		#self.screen.blit( rtxt, (xmax*wx*2+ro,ymax*(wy+gp*5)) )
		rptxt = rpfont.render( self.rain[1]+'%', True, lc )
		(tx,ty) = rptxt.get_size()
		self.screen.blit( rptxt, (xmax*wx*3-tx/2,ymax*(wy+gp*rpl)) )
		icon = pygame.image.load(sd + icons[self.icon[1]]).convert_alpha()
		(ix,iy) = icon.get_size()
		if self.scaleIcon:
			icon2 = pygame.transform.scale( icon, (int(ix*0.5),int(iy*0.5)) )
			(ix,iy) = icon2.get_size()
			icon = icon2
		if ( iy < 90 ):
			yo = (90 - iy) / 2 
		else: 
			yo = 0
		self.screen.blit( icon, (xmax*wx*3-ix/2,ymax*(wy+gp*1.2)+yo-20) )

		# Sub Window 3
		txt = font.render( self.day[2]+':', True, lc )
		(tx,ty) = txt.get_size()
		self.screen.blit( txt, (xmax*(wx*5)-tx/2,ymax*(wy+gp*0)) )
		txt = font.render( self.temps[2][0] + ' / ' + self.temps[2][1], True, lc )
		(tx,ty) = txt.get_size()
		self.screen.blit( txt, (xmax*wx*5-tx/2,ymax*(wy+gp*5)) )
		#self.screen.blit( rtxt, (xmax*wx*4+ro,ymax*(wy+gp*5)) )
		rptxt = rpfont.render( self.rain[2]+'%', True, lc )
		(tx,ty) = rptxt.get_size()
		self.screen.blit( rptxt, (xmax*wx*5-tx/2,ymax*(wy+gp*rpl)) )
		icon = pygame.image.load(sd + icons[self.icon[2]]).convert_alpha()
		(ix,iy) = icon.get_size()
		if self.scaleIcon:
			icon2 = pygame.transform.scale( icon, (int(ix*0.5),int(iy*0.5)) )
			(ix,iy) = icon2.get_size()
			icon = icon2
		if ( iy < 90 ):
			yo = (90 - iy) / 2 
		else: 
			yo = 0
		self.screen.blit( icon, (xmax*wx*5-ix/2,ymax*(wy+gp*1.2)+yo-20) )

		# Sub Window 4
		txt = font.render( self.day[3]+':', True, lc )
		(tx,ty) = txt.get_size()
		self.screen.blit( txt, (xmax*(wx*7)-tx/2,ymax*(wy+gp*0)) )
		txt = font.render( self.temps[3][0] + ' / ' + self.temps[3][1], True, lc )
		(tx,ty) = txt.get_size()
		self.screen.blit( txt, (xmax*wx*7-tx/2,ymax*(wy+gp*5)) )
		#self.screen.blit( rtxt, (xmax*wx*6+ro,ymax*(wy+gp*5)) )
		rptxt = rpfont.render( self.rain[3]+'%', True, lc )
		(tx,ty) = rptxt.get_size()
		self.screen.blit( rptxt, (xmax*wx*7-tx/2,ymax*(wy+gp*rpl)) )
		icon = pygame.image.load(sd + icons[self.icon[3]]).convert_alpha()
		(ix,iy) = icon.get_size()
		if self.scaleIcon:
			icon2 = pygame.transform.scale( icon, (int(ix*0.5),int(iy*0.5)) )
			(ix,iy) = icon2.get_size()
			icon = icon2
		if ( iy < 90 ):
			yo = (90 - iy) / 2 
		else: 
			yo = 0
		self.screen.blit( icon, (xmax*wx*7-ix/2,ymax*(wy+gp*1.2)+yo-20) )

		# Update the display
		pygame.display.update()
		pygame.event.pump()
   
####################################################################
	def disp_status(self):
		# Fill the screen with black
		self.screen.fill( (0,0,0) )
		xmin = 1
		xmax = self.xmax
		ymax = self.ymax
		lines = 2
		lc = (255,255,255)
		lred = (255,0,0)
		lblue = (0,0,255)
		lgreen = (0,255,0) 
		#fn = "freesans"
		fn = "courier"

		# Draw Screen Border
		pygame.draw.line( self.screen, lc, (xmin,0),(xmax,0), lines )
		pygame.draw.line( self.screen, lc, (xmin,0),(xmin,ymax), lines )
		pygame.draw.line( self.screen, lc, (xmin,ymax),(xmax,ymax), lines )	# Bottom
		pygame.draw.line( self.screen, lc, (xmax,0),(xmax,ymax), lines )
		
		# Title
		th = self.tmdateTh
		font = pygame.font.SysFont( fn, int(ymax*th), bold=1 )	# Regular Font
		tm1 = 'System Status'
		rtm1 = font.render( tm1, True, lgreen )
		self.screen.blit( rtm1, (xmin+10,self.tmdateYPos) )
		
 		# Conditions
		st = 0.16    # Yaxis Start Pos
		gp = 0.065   # Line Spacing Gap
		th = 0.06    # Text Height
		dh = 0.05    # Degree Symbol Height
		so = 0.01    # Degree Symbol Yaxis Offset
		xp = 0.52    # Xaxis Start Pos
		x2 = 0.78    # Second Column Xaxis Start Pos

		font = pygame.font.SysFont( fn, int(ymax*th), bold=1 )
    
		# display ip address
		ipaddress = 'No IP Address!'
		if (self.ipaddresseth0 != ''):
      			ipaddress = self.ipaddresseth0
      		elif (self.ipaddresswlan0 != ''):
      			ipaddress = self.ipaddresswlan0
      		else:
      			ipaddress = 'No IP Address!'  
		
		txt = font.render( 'USB Power.....: ' + str(pwr_mode()), True, lgreen )
                self.screen.blit( txt, (xmin+15,ymax*(st+gp*0)) )

		txt = font.render( 'Batt level....: ' + str(bat_percentage()) + ' %',True,lgreen)
		self.screen.blit( txt, (xmin+15,ymax*(st+gp*1)) )
		
		txt = font.render( 'Batt Voltage..: ' + str(bat_level()) + ' mV', True, lgreen )
                self.screen.blit( txt, (xmin+15,ymax*(st+gp*2)) )

		txt = font.render( 'RPi Voltage...: ' + str(rpi_level()) + ' mV', True, lgreen )
                self.screen.blit( txt, (xmin+15,ymax*(st+gp*3)) )

		txt = font.render( 'Batt Status...: ' + str(bat_charging()), True, lgreen )
		self.screen.blit( txt, (xmin+15,ymax*(st+gp*4)) )

		txt = font.render( 'Batt Temp.....: ' + str(pico_temp()) + ' C', True, lgreen)
                self.screen.blit( txt, (xmin+15,ymax*(st+gp*5)) )

		txt = font.render( 'IP Address....: ' + ipaddress, True, lgreen )
		self.screen.blit( txt, (xmin+15,ymax*(st+gp*6)) )
		
		# Update the display
		pygame.display.update()
   

	####################################################################
	def sPrint( self, s, font, x, l, lc ):
		f = font.render( s, True, lc )
		self.screen.blit( f, (x,self.ymax*0.075*l) )

# Helper function to which takes seconds and returns (hours, minutes).
############################################################################
def stot( sec ):
	min = sec.seconds // 60
	hrs = min // 60
	return ( hrs, min % 60 )


# Given a sunrise and sunset time string (sunrise example format '7:00 AM'),
# return true if current local time is between sunrise and sunset. In other
# words, return true if it's daytime and the sun is up. Also, return the 
# number of hours:minutes of daylight in this day. Lastly, return the number
# of seconds until daybreak and sunset. If it's dark, daybreak is set to the 
# number of seconds until sunrise. If it daytime, sunset is set to the number 
# of seconds until the sun sets.
# 
# So, five things are returned as:
#  ( InDaylight, Hours, Minutes, secToSun, secToDark).
############################################################################
def Daylight( sr, st ):
	inDaylight = False	# Default return code.

	# Get current datetime with tz's local day and time.
	tNow = datetime.datetime.now()

	# From a string like '7:00 AM', build a datetime variable for
	# today with the hour and minute set to sunrise.
	t = time.strptime( sr, '%I:%M %p' )		# Temp Var
	tSunrise = tNow					# Copy time now.
	# Overwrite hour and minute with sunrise hour and minute.
	tSunrise = tSunrise.replace( hour=t.tm_hour, minute=t.tm_min, second=0 )
	
	# From a string like '8:00 PM', build a datetime variable for
	# today with the hour and minute set to sunset.
	t = time.strptime( myDisp.sunset, '%I:%M %p' )
	tSunset = tNow					# Copy time now.
	# Overwrite hour and minute with sunset hour and minute.
	tSunset = tSunset.replace( hour=t.tm_hour, minute=t.tm_min, second=0 )

	# Test if current time is between sunrise and sunset.
	if (tNow > tSunrise) and (tNow < tSunset):
		inDaylight = True		# We're in Daytime
		tDarkness = tSunset - tNow	# Delta seconds until dark.
		tDaylight = 0			# Seconds until daylight
	else:
		inDaylight = False		# We're in Nighttime
		tDarkness = 0			# Seconds until dark.
		# Delta seconds until daybreak.
		if tNow > tSunset:
			# Must be evening - compute sunrise as time left today
			# plus time from midnight tomorrow.
			tMidnight = tNow.replace( hour=23, minute=59, second=59 )
			tNext = tNow.replace( hour=0, minute=0, second=0 )
			tDaylight = (tMidnight - tNow) + (tSunrise - tNext)
		else:
			# Else, must be early morning hours. Time to sunrise is 
			# just the delta between sunrise and now.
			tDaylight = tSunrise - tNow

	# Compute the delta time (in seconds) between sunrise and set.
	dDaySec = tSunset - tSunrise		# timedelta in seconds
	(dayHrs, dayMin) = stot( dDaySec )	# split into hours and minutes.
	
	return ( inDaylight, dayHrs, dayMin, tDaylight, tDarkness )


############################################################################
class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.kill_now = True

#==============================================================
killer = GracefulKiller()

# Create an instance of the lcd display class.
myDisp = SmDisplay()

running = True		# Stay running while True
s = 0			# Seconds Placeholder to pace display.
dispTO = 0		# Display timeout to automatically switch back to weather dispaly.

# Loads data from Weather.com into class variables.

#if myDisp.UpdateWeather() == False:
#	pygame.quit() # quit if we cannot get an initial weather update (ie: no ip address, etc.)
#	sys.exit(1)
myDisp.UpdateWeather()
myDisp.disp_weather()
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
while running:
		if (killer.kill_now == True):
			pygame.quit()
			sys.exit()

		# Look for and process keyboard events to change modes.
        	#for event in pygame.event.get():
        	#	if (event.type == pygame.KEYUP and event.key == pygame.K_c and event.mod & pygame.KMOD_CTRL):
            	#		pygame.quit()
            	#		sys.exit()

		try:
			# Refresh the display after each second.
			if (s != time.localtime().tm_sec):
				s = time.localtime().tm_sec
				myDisp.disp_weather()
				if (s == 0): # update the weather once per minute, on the "00" second
					print "updating weather debug"
					myDisp.UpdateWeather()
				# show the weather radar image for 10 seconds
				if ( s == 10 ):
					try:
				    		# (r, g, b) color tuple, values 0 to 255
				    		white = (255, 255, 255)
				    		# create a 600x400 white screen
				    		screen = pg.display.set_mode((320,240),  pg.RESIZABLE )
				    		screen.fill(white)
				    		# load the image from a file or stream
				    		#image = pg.image.load(image_file)
				    		image = pg.image.load("radar.jpg")
						image = pg.transform.scale(image, (320,240))
				    		# draw image, position the image ulc at x=20, y=20
				    		screen.blit(image, (0, 0))
				    		pg.display.flip()
				    		time.sleep(10) # show the radar for 10 seconds
					except:
						print "Unexpected Radar error:", sys.exc_info()[0]
						pass # if we can't load the radar image, no problem, just keep displaying the weather            		

					# Display system status for 9 seconds
					try:
						myDisp.disp_status()
						time.sleep(9)
					except:
						print "Unexpected disp status error:", sys.exc_info()[0]
						pass
		except:
			print "Unexpected weather loading error:", sys.exc_info()[0]
			pass # if we can't load the weather, just keep going. We might have lost network connection and it might come back.
		
		# Loop timer.
		pygame.time.wait( 900 )

pygame.quit()
sys.exit()
