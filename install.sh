#!/bin/bash

mkdir -p "/var/log/artemis"
mkdir -p "/usr/local/bin/artemis"
mkdir -p "/tmp/artemis"

sudo cp *.py "/usr/local/bin/artemis"
sudo python3.4 setup.py install

