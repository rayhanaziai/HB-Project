#!/bin/bash

# cd ~/vagrant
# vagrant up
# vagrant ssh
cd /home/vagrant/src/project
source env/bin/activate
source secrets.sh
python sendpayment.py
