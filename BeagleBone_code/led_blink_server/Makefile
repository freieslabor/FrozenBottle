

all: led led0.bin led1.bin

clean:
	rm led led0.bin led1.bin

led: led_main.c ./prussdrv.c ./prussdrv.h ./pruss_intc_mapping.h read_text.h read_text.c commands.c commands.h fix_values.h fix_values.c
	gcc -o led -Wall -I. -ggdb -O0 led_main.c ./prussdrv.c read_text.c commands.c fix_values.c -lm


# Assemble the PRU code
led0.bin : led0.p PRUtime.hp
	../utils/pasm -V2b led0.p

led1.bin : led1.p PRUtime.hp
	../utils/pasm -V2b led1.p


