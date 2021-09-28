#!/bin/bash
# testpowersavingmode.sh
# This script tests the power-saving scripts.
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

sudo ./powerstatestatus.sh
sudo ./backlightoff.sh
sudo ./hdmioff.sh
sudo ./ledsoff.sh
sudo ./usbpoweroff.sh

sleep 1200

sudo ./backlighton.sh
sudo ./hdmion.sh
sudo ./ledson.sh
sudo ./usbpoweron.sh
sudo ./powerstatestatus.sh
