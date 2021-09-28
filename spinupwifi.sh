#!/bin/bash

# try to connect to known wifi network. If that fails, create an adhoc network as a fallback.

exec 1> >(logger -s -t $(basename $0)) 2>&1 # log everything to syslog

source ./config.txt
ssid1=$SSID1

connectionlevel=0
exitcode=0
# **************************************************************************
createAccessPoint(){
    echo "Creating WiFi Access Point..."
    ifconfig wlan0 down
    ifconfig wlan0 192.168.3.1 netmask 255.255.255.0 up
    hostapd -B /etc/hostapd/hostapd.conf
    echo "Starting DCHP Server..."
    /usr/sbin/dhcpd wlan0

    # check that wlan0 is now online
    wlan=`/sbin/ifconfig wlan0 | grep inet\ addr | wc -l`
    if [ $wlan -eq 0 ]; then # if it isn't online
        echo "wlan interface is down! Attempting to bring it up again!"
	/sbin/ifdown wlan0 && /sbin/ifup wlan0 # try to bring it up again
	wlan=`/sbin/ifconfig wlan0 | grep inet\ addr | wc -l`
	if [ $wlan -eq 0 ]; then # if it is still not online, give up
                echo "wlan interface is still down! Giving up!"
		echo "Unable to create Access Point!"
		connectionlevel=0
	fi
    else # if it is online
        echo "Access Point is Online."
	connectionlevel=2
    fi
}
# ****************************************************************************

# quick hack: scan three times for the SSID's we want

# first, kill dhcpd and hostapd if they are already running
sudo /etc/init.d/networking stop
echo "Killing hostapd, dhcpd, dhclient, wpa_supplicant..."
sudo pkill -f hostapd
sudo pkill -f dhcpd
sudo pkill -f dhclient
sudo pkill -f wpa_supplicant
sudo /etc/init.d/networking start

#ifconfig wlan0 down
#ifconfig wlan0 up

ifdown wlan0
ifup wlan0

# Now scan and connect
ssids=( $ssid1 )
wifidhcpconnected=false
printf "Scanning for known Wifi networks..."
for ssid in "${ssids[@]}"
do
    printf "."
    if iwlist wlan0 scan | grep $ssid > /dev/null
    then
        wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null 2>&1
        printf "\n"
        echo "Connected to: " $ssid
	echo "Attempting to get DHCP ip address..."
	if dhclient -1 wlan0
        then
            echo "Got DHCP ip address."
	    wifidhcpconnected=true
	    wget -q --tries=10 --timeout=20 --spider http://www.google.com
	    if [[ $? -eq 0 ]]; then
                echo "Connected to Internet."
            	connectionlevel=4
	    else
                echo "Not connected to Internet."
		connectionlevel=3
	    fi
            break
        else
            echo "Could not get DHCP Address."
            wpa_cli terminate
	    connectionlevel=1
            break
        fi
    else
        echo "Not in range, WiFi with SSID:" $ssid
    fi
    sleep 1s
done

# if no known wifi networks found, turn pi into it's own access point
if ! $wifidhcpconnected; then
    echo "No known Wifi network found."
    createAccessPoint
fi

# inform the user about the final wifi connection status
#if [ $connectionlevel == 4 ]; then
   #echo "Wifi OK. Accessible OK. Internet OK."
#   echo ""
#fi

#if [ $connectionlevel == 3 ]; then
   #echo "Wifi OK. Accessible OK. Internet NOT OK."
#   echo ""
#fi

#if [ $connectionlevel == 2 ]; then
   #echo "Pi is connected to Self-Access-Point and is accessible"
#   echo ""
#fi

if [ $connectionlevel == 1 ]; then
   #echo "pi is not accessible! Did not receive DHCP address!"
   exitcode=1
fi

if [ $connectionlevel == 0 ]; then
   #echo "pi is not accessible! Wifi adapter is down and not recoverable!"
   exitcode=1
fi

# display the ip addresses
eth0ip=$(ifconfig eth0 | grep "inet addr" | cut -d ':' -f 2 | cut -d ' ' -f 1)
wlan0ip=$(ifconfig wlan0 | grep "inet addr" | cut -d ':' -f 2 | cut -d ' ' -f 1)
myssid=$(iwgetid -r)

echo "SSID  : ${myssid} "
echo "wlan0 : ${wlan0ip} "
echo "eth0  : ${eth0ip} "

exit $exitcode


