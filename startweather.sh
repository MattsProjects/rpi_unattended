#!/bin/bash
# startweather.sh
# This script starts the example weather display application
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
echo "Starting Weather app in background with stdout and stderr in log file..."
sudo python /usr/local/bin/rpi_unattended/weather.py >> /usr/local/bin/rpi_unattended/weather.log 2>&1 &
echo "Weather app now running in background. See weather.log..."
