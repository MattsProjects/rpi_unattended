#!/bin/bash
# backlightoff.sh
# Script for turning the backlight of the piTFT 2.8" screen off.
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

# Jessie
sudo sh -c 'echo "0" > /sys/class/backlight/soc\:backlight/brightness'
# wheezy
#sudo sh -c "echo 508 > /sys/class/gpio/export"
#sudo sh -c "echo 'out' > /sys/class/gpio/gpio508/direction"
#sudo sh -c "echo '0' > /sys/class/gpio/gpio508/value"
exit $?
