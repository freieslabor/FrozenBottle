

all: led led0.bin led1.bin

clean:
	rm led led0.bin led1.bin

led: led_main.c ../ti_pru_code/prussdrv.c ../ti_pru_code/prussdrv.h ../ti_pru_code/pruss_intc_mapping.h
	gcc -o led -Wall -I. -ggdb -O0 led_main.c ../ti_pru_code/prussdrv.c


# Assemble the PRU code
led0.bin : led0.p PRUtime.hp
	../utils/pasm -V2b led0.p

led1.bin : led1.p PRUtime.hp
	../utils/pasm -V2b led1.p


