#!/bin/bash

IP=""

cd /opt/FrozenBottle/UDP_clients/

while [ "$IP" == "" ]; do
       IP=$(ip addr | grep 'state UP' -A2 | grep "inet " | tail -n1 | awk '{print $2}' | cut -f1  -d'/')
       sleep 1
done

python2.7 text.py localhost "$IP"

