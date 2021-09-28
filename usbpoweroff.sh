#!/bin/bash

# Power-cycle the Raspberry Pi USB bus to reset attached USB devices
#
# Released under MIT license. See the accompanying LICENSE.txt file for
# full terms and conditions
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# try to connect to known wifi network. If that fails, create an adhoc network as a fallback.
# **************************************************************************
source /usr/local/bin/rpi_unattended/config.txt
ssid1=$SSID1

connectionlevel=0

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
spinUpWifi(){
  # quick hack: scan three times for the SSID's we want.
  ssids=( $ssid1 )
  wifidhcpconnected=false
  echo "Scanning for known Wifi networks..."
  for ssid in "${ssids[@]}"
  do
      printf "."
      if iwlist wlan0 scan | grep $ssid > /dev/null
      then
	  wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null 2>&1
	  printf "\n"
	  echo "[ ok ] Connected to: " $ssid
	  echo "Attempting to get DHCP ip address..."
	  if dhclient -1 wlan0
	  then
	      echo "[ ok ] Get DHCP ip address" $ssid
	      wifidhcpconnected=true
	      wget -q --tries=10 --timeout=20 --spider http://www.google.com
	      if [[ $? -eq 0 ]]; then
		  echo "[ ok ] Internet connection test"
		  connectionlevel=4
	      else
		  echo "[FAIL] Internet connection test"
		  connectionlevel=3
	      fi
	      break
	  else
	      echo "[FAIL] Get DHCP ip address"
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
  if [ $connectionlevel == 4 ]; then
    echo "pi is connected to Wifi and is accessible and can access internet"
  fi

  if [ $connectionlevel == 3 ]; then
    echo "pi is connected to Wifi and is accessible, but cannot see internet"
  fi

  if [ $connectionlevel == 2 ]; then
    echo "Pi is connected to Self-Access-Point and is accessible"
  fi

  if [ $connectionlevel == 1 ]; then
    echo "pi is not accessible! Did not receive DHCP address!"
  fi

  if [ $connectionlevel == 0 ]; then
    echo "pi is not accessible! Wifi adapter is down and not recoverable!"
  fi

  # display the ip addresses
  eth0ip=$(ifconfig eth0 | grep "inet addr" | cut -d ':' -f 2 | cut -d ' ' -f 1)
  wlan0ip=$(ifconfig wlan0 | grep "inet addr" | cut -d ':' -f 2 | cut -d ' ' -f 1)
  myssid=$(iwgetid -r)

  echo "  SSID  : ${myssid} "
  echo "  wlan0 : ${wlan0ip} "
  echo "  eth0  : ${eth0ip} "
}

# Raspberry Pi 1 running Raspbian Wheezy
FILE=/sys/devices/platform/bcm2708_usb/buspower
if [ ! -e $FILE ]; then
# Raspberry Pi 2 running Raspbian Jessie
    FILE=/sys/devices/platform/soc/3f980000.usb/buspower
fi
if [ -e $FILE ]; then
    echo "stopping networking..."
    sudo /etc/init.d/networking stop
    sleep 0.1
    echo "powering down usb bus..."
    sudo pkill -f unplug2shutdown
    echo 0 > $FILE
  #  sleep 60
  #  echo "powering up usb bus..."
  #  echo 1 > $FILE
  #  sleep 2
  #  echo "starting networking..."
  #  sudo /etc/init.d/networking start
  #  spinUpWifi
else
    echo "Could not find a known USB power control device. Checking /sys/devices/platform/:"
    find /sys/devices/platform/* | grep buspower
fi
