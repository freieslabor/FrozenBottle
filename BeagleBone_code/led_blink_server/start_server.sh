#!/bin/sh

MY_PATH="`dirname \"$0\"`"

#cd /home/labor/GIT_progs/BBBPRU/led_blink/
cd -- ${MY_PATH}
./led -l0 50 -l1 125

