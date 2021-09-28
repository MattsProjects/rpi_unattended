#!/bin/bash
# systemmailer.sh
# sends various alerts via email depending on command line arguments
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

exec 1> >(logger -s -t $(basename $0)) 2>&1

alert=""
source /usr/local/bin/rpi_unattended/config.txt
toaddress=$EMAIL_ADD_TO
phoneaddress=$EMAIL_ADD_TO_PHONE
# Parse the command line argument.
case "$1" in
	startup)
		alert="Startup"
		;;
	shutdown)
		alert="Shutdown"
		;;
	powerlost)
		alert="USB Power Lost"
		;;
	powerrestored)
		alert="USB Power Restored"
		;;
	custom)
		if [[ $2 = "" ]]; then
			echo $"Usage: $0 {startup|shutdown|powerlost|powerrestored|custom myOneWordmessage toaddress@domain.com}"
			exit 1
		else
			alert=$2
			toaddress=$3
		fi
		;;
	*)
		echo $"Usage: $0 {startup|shutdown|powerlost|powerrestored|custom myOneWordmessage toaddress@domain.com}"
		exit 1
esac

# variables that are common to all alerts
hostname=$(hostname)
timestamp=$(date)
emailsubject="[${hostname}] Alert: ${alert}"

# Startup: send email with system logs
if [[ $alert = "Startup" ]]; then
	# pull the ip address of the system
	eth0ip=$(echo "eth0 : $(/sbin/ifconfig eth0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}')")
	wlan0ip=$(echo "wlan0: $(/sbin/ifconfig wlan0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}')")
	ssid=$(echo "SSID : $(iwgetid -r)")

	# email variables
	emailbody="$alert \n$timestamp \n$eth0ip \n$wlan0ip \n$ssid \n"

	# collect some log files
	logpath=/usr/local/bin/rpi_unattended
	sudo cp /var/log/syslog $logpath/syslog.txt
	sudo cp /var/log/boot $logpath/bootlogd.txt
	sudo cp /var/log/rclocal.log $logpath/rclocal.txt
	sudo dmesg > $logpath/dmesg.txt

	file1=$logpath/syslog.txt
	file2=$logpath/bootlogd.txt
	file3=$logpath/rclocal.txt
	file4=$logpath/dmesg.txt

	echo -e $emailbody | mutt -s "$emailsubject" -a $file1 -a $file2 -a $file3 -a $file4 -- $toaddress
	echo -e $emailbody | mutt -s "$emailsubject" -- $phoneaddress

# Shutdown: send email with...
elif [[ $alert = "Shutdown" ]]; then
	emailbody="$alert \n$timestamp \n"

	#file1=$logpath/shutdownpowerstatus.txt

	#echo -e $emailbody | mutt -s "$emailsubject" -a $file1 -- $toaddress
	echo -e $emailbody | mutt -s "$emailsubject" -- $toaddress
	echo -e $emailbody | mutt -s "$emailsubject" -- $phoneaddress 

# power lost/restored: Send a text message via email
elif [[ $alert = "USB Power Lost" ]] || [[ $alert = "USB Power Restored" ]]; then
	emailbody="$alert \n$timestamp"
	echo -e $emailbody | mutt -s "$emailsubject" -- $toaddress

# custom
elif [[ $1 = "custom" ]]; then
        emailbody="$alert \n$timestamp \n"
        echo -e $emailbody | mutt -s "$emailsubject" -- $toaddress

# else
else
	echo "Shouldn't get here..."
	echo $alert
fi

exit $?

