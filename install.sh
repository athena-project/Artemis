#!/bin/bash

LOG = /var/log/artemis

mkdir -p $LOG

sudo python3.4 setup.py install
