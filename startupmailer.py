# startupmailer.py
# This script runs after bootup and sends an email with some log files.
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
# Borrows some code from Cody Giles under the Creative Commons Attribution-ShareAlike 3.0 Unported License

import subprocess
import smtplib
from email import Encoders
from email.MIMEBase import MIMEBase
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import subprocess
import datetime
import time
import sys
import os
import StringIO
import ConfigParser

# load configuation (email addresses, etc. from a simple config.txt file)
# our config file in this case doesn't have a header (because we also use it for bash scripts).
# so we add the header by bringing the config file in as a string.
dummy = StringIO.StringIO()
dummy.write('[TOP]\n')
dummy.write(open('./config.txt').read())
dummy.seek(0, os.SEEK_SET)
config = ConfigParser.ConfigParser()
config.readfp(dummy)
email_add_to = config.get('TOP','EMAIL_ADD_TO')
email_add_from = config.get('TOP','EMAIL_ADD_FROM')
email_password = config.get('TOP','EMAIL_ADD_FROM_PASSWORD')

def connect_type(word_list):
    """ This function takes a list of words, then, depeding which key word, returns the corresponding
    internet connection type as a string. ie) 'ethernet'.
    """
    if 'wlan0' in word_list or 'wlan1' in word_list:
        con_type = 'wlan'
    elif 'eth0' in word_list:
        con_type = 'eth'
    else:
        con_type = 'current'

    return con_type
try:
	arg='ip route list'  # Linux command to retrieve ip addresses.
	# Runs 'arg' in a 'hidden terminal'.
	p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
	data = p.communicate()  # Get data from 'p terminal'.
  
	# Split IP text block into three, and divide the two containing IPs into words.
	numlines = 0
	ip_lines = data[0].splitlines()
	for line in ip_lines:
  		numlines += 1
  
	split_line_a = ip_lines[numlines-2].split()
	split_line_b = ip_lines[numlines-1].split()
  
	# con_type variables for the message text. ex) 'ethernet', 'wifi', etc.
	ip_type_a = connect_type(split_line_a)
	ip_type_b = connect_type(split_line_b)
  
	"""Because the text 'src' is always followed by an ip address,
	we can use the 'index' function to find 'src' and add one to
	get the index position of our ip.
	"""
  
	if 'src' in split_line_a:
		ipaddr_a = split_line_a[split_line_a.index('src')+1]
	else:
		ipaddr_a = "xxx.xxx.xxx.xxx"
  
	if 'src' in split_line_b:
		ipaddr_b = split_line_b[split_line_b.index('src')+1]
	else:
		ipaddr_b = "xxx.xxx.xxx.xxx"
  
	# Creates a sentence for each ip address.
	if ipaddr_a != 'xxx.xxx.xxx.xxx':
  		my_ip_a = 'Your %s ip is %s' % (ip_type_a, ipaddr_a)
		remote_a = 'http://%s' % (ipaddr_a)
	else:
		my_ip_a = ''
		remote_a = ''
	if ipaddr_b != 'xxx.xxx.xxx.xxx':
		my_ip_b = 'Your %s ip is %s' % (ip_type_b, ipaddr_b)
		remote_b = 'http://%s' % (ipaddr_b)
	else:
		my_ip_b = ''
		remote_b = ''

	# collect the logs. sleep for a few seconds to make sure they've captured everything
	time.sleep(5)
        subprocess.call(["cp", "/var/log/syslog", "./syslog.log"])
	subprocess.check_output('dmesg > ./dmesg.log',shell=True)
	subprocess.call(["cp", "/var/log/rclocal.log", "./rclocal.log"])
	subprocess.call(["cp", "/var/log/boot","./bootlogd.log"])
  
	# Email Account Information
	to = email_add_to # Email to send to.
	gmail_user = email_add_from # Email to send from. (MUST BE GMAIL)
	gmail_password = email_password # Gmail password
	smtpserver = smtplib.SMTP('smtp.gmail.com', 587, None, 30) # Server to use.
	smtpserver.ehlo()  # Says 'hello' to the server
	smtpserver.starttls()  # Start TLS encryption
	smtpserver.ehlo()
	smtpserver.login(gmail_user, gmail_password)  # Log in to server
	today = datetime.datetime.now()  # Get current time/date
  
	# Creates the text, subject, 'from', and 'to' of the message.
	msg = MIMEMultipart()
	msg['Subject'] = 'RPi_Booted'
	msg['From'] = gmail_user
	msg['To'] = to
	msg.attach( MIMEText(today.strftime('%a %b %d %Y, %H:%M:%S %Z %z') + "\n" + my_ip_a + "\n" + my_ip_b + "\n" + "\n" + "Access system remotely at:\n" + remote_a + "\n" + remote_b))
  
  # Try to attach boot logs
	try:
  		# pull the syslog
		fileName = "./syslog.log"
	  	f = file(fileName)
  		attachment = MIMEText(f.read())
	  	attachment.add_header('Content-Disposition', 'attachment', filename=fileName)
	  	msg.attach(attachment)
  
  		# pull dmesg output
	  	fileName2 = "./dmesg.log"
	  	f2 = file(fileName2)
  		attachment2 = MIMEText(f2.read())
	  	attachment2.add_header('Content-Disposition', 'attachment', filename=fileName2)
  		msg.attach(attachment2)
  	
	  	# pull the custom rclocal.log created by the rc.local script
  		fileName3 = "./rclocal.log"
	  	f3 = file(fileName3)
  		attachment3 = MIMEText(f3.read())
	  	attachment3.add_header('Content-Disposition', 'attachment', filename=fileName3)
  		msg.attach(attachment3)
  
	  	# pull the boot log
        	fileName3 = "./bootlogd.log"
	        f3 = file(fileName3)
        	attachment3 = MIMEText(f3.read())
	        attachment3.add_header('Content-Disposition', 'attachment', filename=fileName3)
        	msg.attach(attachment3)
	except:
  		print "Error attaching boot logs: ", sys.exc_info()[0]
		msg.attach(MIMEText("\n Error attaching boot logs: " + str(sys.exc_info()[0])))
  	
	# Sends the email
	try:
  		smtpserver.sendmail(gmail_user, [to], msg.as_string())
	except:
		print 'Email not sent.'
	# Closes the smtp server.
	smtpserver.quit()
except:
	print("Error (socket error means smtplib.smtp probably timed out):", sys.exc_info()[0])
	sys.exit()
