#!/bin/bash

IP="127.0.0.1"
PORT=""
DURATION=15.0

animNumb=7

declare -a arr=(
#"blue.py"
"ddmaze.py"
"colorFlow.py"
# braucht arguzment "colorText.py"
"colorWheel.py"
## kaputt "erlenmeyer.py"
#"game_of_hive.py"
#"gif_scroll.py"
#"hex.py"
#"maze.py"
#"mrburns.py"
#"photo.py"
"plasma.py"
"snake.py"
"snow_tetris.py"
# kaputt. "import command not found"  wtf???  "spriteMove.py"
# bug. irgendwas komisches.   "tetris.py"
# bug. import: command-not-fond  "text.py"
#"white.py"
)

exit_script()
{
    echo "Exiting."
	trap - SIGINT SIGTERM
    kill -- -$$ # Sends SIGTERM to child/sub processes
}

trap exit_script SIGINT SIGTERM

cd "$(dirname "$0")"

while true
do

declare -a finarr=()
lastrand=1000


#Includes Random
for i in $animNumb
do

    rand=$RANDOM%$animNumb
    if $rand!=$lastrand
    then
        rand=$rand+$rand%[$animNumb-1]+1
    fi
    finarr+=${arr[$rand]}
    
done
    

## now loop through the above array
for i in "${finarr[@]}"
do
	echo "$i"
	"./${i}" "${IP}" &
	PID=$!
	sleep ${DURATION}
	kill -15 ${PID}
	# or do whatever with individual element of the array
done

done
