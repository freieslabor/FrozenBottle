#!/bin/bash

IP="151.217.115.43"
PORT=""
DURATION=15.0


declare -a arr=(
#"blue.py"
"colorFlow.py"
# braucht arguzment "colorText.py"
"colorWheel.py"
## kaputt "erlenmeyer.py"
#"game_of_hive.py"
"gif_scroll.py"
#"hex.py"
"maze.py"
"mrburns.py"
"photo.py"
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

while true
do

## now loop through the above array
for i in "${arr[@]}"
do
	echo "$i"
	"./${i}" "${IP}" &
	PID=$!
	sleep ${DURATION}
	kill -15 ${PID}
	# or do whatever with individual element of the array
done

done
