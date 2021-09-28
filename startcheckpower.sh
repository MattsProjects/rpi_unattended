#!/bin/bash
# startcheckpower.sh
# This script is to run at bootup to run the checkpower.py script in the background
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
echo "Starting checkpower.py"
sudo python -u /usr/local/bin/rpi_unattended/checkpower.py & # the -u is needed to get console ouptut when sleeping (unbuffered output)
echo "checkpower.py now running in background..."

