#!/bin/bash

# Run some programs for the FrozenBottle in an endless-loop.
# list of programs is in the bash-array 'progs' in first line.

STAYTIME=19

    # left out photo.py, as it uses PIL...
declare -a progs=("./colorFlow.py" "./blue.py" "./colorWheel.py" "./snake.py" "./spriteMove.py")

if [ -z "$1" ]; then
  echo "missing argument for target address" >&2
  exit 1
fi
ADDR=$1

RED='\033[0;31m'
HL='\033[0;36m'
NC='\033[0m' # No Color

function cleanup {
  if [ -z "$PID" ]; then
    false
  else
    kill $PID
    wait $PID
  fi
}

function runit {
  echo -e "${HL}running $1 $NC"
#  trap "echo breaking $PID; kill $PID; return 1" SIGINT SIGTERM
  trap "cleanup;return 1" SIGINT SIGTERM SIGHUP
  "$1" $2 &
  PID=$!
  echo pid = $PID
  for i in `seq 1 $STAYTIME`; do
    sleep 1
    if kill -0 "$PID" >/dev/null 2>&1; then
      #echo TRUE $?
      true # is still running.
    else
      #echo FALSE $?
      break
    fi
  done
  # if still running here, consider ok.
  if kill -0 "$PID" >/dev/null 2>&1; then
    # runs. So we will return OK.
    RETVAL=0
  else
    echo -e "${RED}$1 exited early.$NC" >&2
    RETVAL=1
  fi
  kill $PID >/dev/null 2>&1
  wait $PID
  trap - SIGINT SIGTERM SIGHUP
  return $RETVAL
}



while [ 1 ]
do
  for prg in "${progs[@]}"; do
    runit "$prg" $ADDR
    if [ $? -ne 0 ]; then
      echo "exiting." 1>&2;exit 1
    fi
    sleep 1
  done
done

