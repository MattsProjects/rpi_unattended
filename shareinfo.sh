#!/bin/bash
# shareinfo.sh
# This script shows an example of reading/writing to a file.
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
echo "Writing information to file..."
echo 1 | sudo tee ./isalive
echo "Reading information from file..."
echo $(cat ./isalive)
echo "Writing information to file..."
echo A | sudo tee ./isalive
echo "Reading information from file..."
echo $(cat ./isalive)
echo $info
