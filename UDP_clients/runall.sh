#!/bin/bash

declare -a progs=("./colorFlow.py" "./blue.py" "./colorWheel.py" "./snake.py")

if [ -z "$1" ]; then
  echo "missing argument for target address" >&2
  exit 1
fi
ADDR=$1

function cleanup {
  if [ -z "$PID" ]; then
    false
  else
    kill $PID
    wait $PID
  fi
}

function runit {
  echo running $1
#  trap "echo breaking $PID; kill $PID; return 1" SIGINT SIGTERM
  trap "cleanup;return 1" SIGINT SIGTERM SIGHUP
  "$1" $2 &
  PID=$!
  echo pid = $PID
  for i in `seq 1 10`; do
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
    # runs. so kill and return OK.
    kill $PID >/dev/null 2>&1
    wait $PID
    return 0
  fi
  kill $PID >/dev/null 2>&1
  wait $PID
  trap - SIGINT SIGTERM SIGHUP
  return 1
}



while [ 1 ]
do
  for prg in "${progs[@]}"; do
    runit "$prg" $ADDR
    if [ $? -ne 0 ]; then
      echo "failed. exiting." 1>&2;exit 1
    fi
    sleep 1
  done
done

