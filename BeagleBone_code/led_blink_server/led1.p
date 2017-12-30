// PRU assembler code for PRU unit #0

.origin 0

//#include "../ti_pru_code/PRU.hp"

MEMACCESSPRUDATARAM:



// LED Kram.
//#define NEG_LOGIC_OUT


	// skip code in 'zeropage'.
	jmp start_here

#include "./PRUtime.hp"



start_here:
	ldi r23,#0x2000 // stack



	jal r24, PRU1_timer_init


	// spin until dead.
_loop:
	and r0,r0,r0
	jmp _loop


	halt




