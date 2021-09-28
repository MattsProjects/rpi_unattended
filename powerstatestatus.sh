#!/bin/bash
# powerstatestatus.sh
# This script echo's the power state of various hardware components.
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

# status of HDMI power
sudo /opt/vc/bin/tvservice -s | grep 'off' &> /dev/null
if [ $? == 0 ]; then
	echo "HDMI Power State............:  Off"
else
	echo "HDMI Power State............:  On"
fi

# status of backlight
cat /sys/class/gpio/gpio508/value | grep '1' &> /dev/null
if [[ $? == 0 ]];then
	echo "TFT Backlight Power State...:  On"
else
	echo "TFT Backlight Power State...:  Off"
fi

# status of USB ports
cat /sys/devices/platform/soc/3f980000.usb/buspower | grep '0x1' &> /dev/null
if [[ $? == 0 ]]; then
        echo "USB Bus Power State.........:  On"
else
        echo "USB Bus Power State.........:  Off"
fi

# status of LED's
cat /sys/class/leds/led0/brightness | grep '255' &> /dev/null
if [[ $? == 0 ]];then
	echo "RPi Green LED Power State...:  On"
else
	echo "RPi Green LED Power State...:  Off"
fi
	
cat /sys/class/leds/led1/brightness | grep '255' &> /dev/null
if [[ $? == 0 ]];then
        echo "RPi Red LED Power State..,,.:  On"
else
        echo "RPi Red LED Power State,,...:  Off"
fi

# temperature of CPU
cputemp=$(/opt/vc/bin/vcgencmd measure_temp)
cputemp=${cputemp:5}
echo "CPU Temp is.................: " $cputemp

# temperature of PicoUP
picotemp=$(sudo i2cget -y 1 0x69 0x1b b)
picotemp=${picotemp:2}
echo "Pico UPS Temp is............: " $picotemp"'C"
