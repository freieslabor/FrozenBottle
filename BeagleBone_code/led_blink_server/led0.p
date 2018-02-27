// PRU assembler code for PRU unit #0

.origin 0

#include "./PRU.hp"

//#define NEG_LOGIC_OUT


// interface mit C programm:
// im PRU #0 RAM an 0x0800 liegen zwei bytes (le) mit Zahl-der-bytes,
// danach die bytes für die LED streifen. Diese werden stumpf ausgegeben.
// Gamma und RGB-swapping muss das C Programm machen.
//
// Beim Start wird in addresse 4,5 die Werte für level0,level1 erwartet.
// Wenn sie Null sind, nimmt er defaults an.



// Ausgangs-bits sind in R30, bei PRU0 in 8..13, PRU1 in 0..5   (???)
// mit PIN_MX=0 routet das nach  pr1_pru0_pru_r30[13:8]
// Laut block-diagramm (links) geht das 'enhanced GPIO' nach pins pr1_pru0_pru_r30[15:0]

// Kapitel 9.1 im TI Tech-Ref-Manual "Control Module" koennte weiterhelfen...
//   register-map (mit pin-mux-regs!) in  "Table 9-10. CONTROL_MODULE REGISTERS"

// im sysfs gibt's irgendwie die pins:
//   sudo cat /sys/kernel/debug/pinctrl/44e10800.pinmux/pins

// 4 output pins sind mii1_tx0..3 , register 0x44E10928 .. 0x44E1091C
// 4 input pins sind  mii1_rx0..3 , register 0x44E10940 .. 0x44E10934
// linux-def nach boot is mode 0 im TX, und ox30 im RX modus.
// pullup/down off:   0x18
// pullup:            0x10
// pulldown:          0x00
// to enable receiver, add 0x20

// Die pins "pr1_pru0_r30_0..7" sind auf pinmux-regs 0x0990..




// Eine struktur mit irgendwie allem drin.
.struct Selff
  .u32 reg_ctrl    // pointer to PRUs status reg. (0x00022000)
  .u32 stack
  .u32 cyc_next
  .u16 curLED
  .u16 curBit
  .u32 bits
  .u8 level0
  .u8 level1
.ends

.assign Selff, r16, r21.w0, Self

	// skip code in 'zeropage'.
	jmp start_here


#include "./PRUtime.hp"


start_here:


	// trying 'stuff
	ldi r23,#0x2000 // stack


	// prepare addresses
	ldi r5.w2,#0x0002
	ldi r5.w0,#0x2000
	ldi r6.w2,#0x0002
	ldi r6.w0,#0x4000
	ldi r4,#0

	// enable cycle-count
	lbbo r0, r5, #0, #4
	set r0, #3
	sbbo r0, r5, #0, #4
	ldi r22, #0

	// kick-start other PRU
	ldi r0.w2, #0x0000
	ldi r0.w0, #0x0002
	sbbo r0, r6, #0, #4

	// wait some.
	ldi r0, #1000
  _start_delay:
	sub r0, r0, #1
	qbbc _start_delay, r0, #31

	// copy state of CPUs to mem.
	sbbo r5, r4, #0x20, #4
	lbbo r0, r5, #0x00, #16
	sbbo r0, r4, #0x24, #16
	sbbo r6, r4, #0x40, #4
	lbbo r0, r6, #0x00, #16
	sbbo r0, r4, #0x44, #16

	// read thecounter - diff a few times.
	jal r24, ctr_read_diff
	sbbo r0, r4, #0x80, #4
	jal r24, ctr_read_diff
	sbbo r0, r4, #0x84, #4
	jal r24, ctr_read_diff
	sbbo r0, r4, #0x88, #4
	jal r24, ctr_read_diff2
	sbbo r0, r4, #0x8C, #4
	jal r24, ctr_read_diff
	sbbo r0, r4, #0x90, #4
	jal r24, ctr_read_diff
	sbbo r0, r4, #0x94, #4
	jal r24, ctr_read_diff
	sbbo r0, r4, #0x98, #4
	jal r24, ctr_read_diff2
	sbbo r0, r4, #0x9C, #4

	jal r24, PRU0_timer_read
	sbbo r0, r4, #0x20, #4
	ldi r0, #0x1000
	jal r24, PRU0_timer_wait_until
	sbbo r0, r4, #0x24, #4
	jal r24, PRU0_timer_read
	sbbo r0, r4, #0x24, #4
	jal r24, PRU0_timer_read
	sbbo r0, r4, #0x28, #4
	jal r24, PRU0_timer_read
	sbbo r0, r4, #0x2C, #4

	jmp goto_led_code

	// fall through to the LED code.
//	halt

ctr_read_diff:
	mov r3, r24
	jal r24, PRU0_timer_read
	mov r24,r3
	ldi r1.w2,#0x0002
	ldi r1.w0,#0x4000
	lbbo r1, r1, #0x0C, #4
	sub r0, r0, r1
	jmp r24

ctr_read_diff2:
	mov r3, r24
	jal r24, PRU0_timer_read_reset
	mov r24,r3
	ldi r1.w2,#0x0002
	ldi r1.w0,#0x4000
	lbbo r1, r1, #0x0C, #4
	sub r0, r0, r1
	jmp r24


goto_led_code:
	// setup struct.
	zero &Self, SIZE(Selff)
	ldi r0.w0,0x00022000 & 0x0FFFF
	ldi r0.w2,0x00022000 >> 16
	mov Self.reg_ctrl, r0
	ldi r0, #0
	lbbo Self.level0, r0, #4, #1
	lbbo Self.level1, r0, #5, #1
	ldi r0,#0x1E00
	mov Self.stack, r0
	ldi r0.w0,0x00555555 & 0x0FFFF
	ldi r0.w2,0x00555555 >> 16
	mov Self.bits, r0
//	mov Self.level0, #125-50
//	mov Self.level1, #125

	// clear out our mem up to 0x0800.
	ldi r2,#0x0800
	ldi r0,#0
	ldi r1,#0
_clrmemlop:
	sub r2,r2,#8
	sbbo r0, r2, 0, 8
	qbne _clrmemlop,r2,#0



	// clear PRUs pinmux register and GPIO-config register (C4 is config-space address 0x00026000)
	ldi r0,#0
	sbco  r0, C4, 0x08, 4  // CPCFG0
	sbco  r0, C4, 0x0C, 4  // CPCFG1
	sbco  r0, C4, 0x40, 4  // PIN_MX




/**
 * Wasn das hier?
 * Daten-bus Addressen
 * 0x00000000 .. 0x00002000  PRU eigenen RAM
 * 0x00002000 .. 0x00004000  PRU(andere)  RAM
 * 0x00010000 .. 0x00013000  shared RAM
 * ... misc ...
 * 0x00080000 .. <end>     Host memory mapping.
 *
 *
 * In Doku zu I/O Pins gibt es zwei 8-bit I/O ports.
 * Output port:
 *    pr1_edio_data_out[7:0]      ECAT Digital I/O Data Out
 */




	jal r24, PRU0_timer_init

	ldi r0,#3
	ldi r1,#0x0800  // mem at 0x0800
	sbbo r0, r1, #0, #2


_again:
	// send to LEDs. mem is overwritten by host

	ldi r1,#0x0800  // mem at 0x0800
	ldi r2,#0       // toggle bit #0 in r30
	jal r24,send_led

	jal r24, PRU0_timer_read_reset
	ldi r1, #10000 // pause here?
	add r0, r0, r1
	jal r24,PRU0_timer_wait_until

	jmp _again

#ifdef AM33XX

    // Send notification to Host for program completion
    MOV R31.b0, PRU0_ARM_INTERRUPT+16

#else

    MOV R31.b0, PRU0_ARM_INTERRUPT

#endif

    HALT



// r0 is number of LEDs to fill.
// r1 is address of data.
fillPatt:
	ldi r2, #15
	sbbo r2, r1, #0, #2
	mov r2,#0x15001515
	mov r3,#0x15150015
	mov r4,#0x00151500
	mov r5,#0x00001515
	sbbo r2, r1, #2, #15

	jmp r24



// send a sequence of bits to LED strip.
// clock is 250 ticks per bit.
// r1 is address of data. First two bytes are count. Max 0x1600
// r2.b0 is bit to toggle.
//   cycle-counter must be running, and not be too close to wrapping.
send_led:
	sbbo r24, Self.stack, 0, 4
	sbbo r8, Self.stack, 4, 12
	add Self.stack, Self.stack, #4+12
	mov r9,r1
	mov r10,r2
	lbbo r8, r9, #0, #2
	ldi r0, #0x1600
	qbge _send_led__not_too_many, r8, r0
	ldi r8, #0x1600
  _send_led__not_too_many:
	add r9, r9, #2
	qbeq _send_led_exitloop, r8, #0


	// start with low.
#ifdef NEG_LOGIC_OUT
	set r30, r10.b0
#else
	clr r30, r10.b0
#endif

	ldi Self.curLED, #0
	ldi Self.curBit, #0xFF  // start with empty bits reg.

	// start value for cyc_next
	jal r24, PRU0_timer_read
	add r0,r0,#50
	mov Self.cyc_next, r0

	// TODO: fetch first byte, or jump into the get-next-byte place in loop.

  _send_led_loop:
	// check to get next byte
	qbbc _send_led__no_new_byte, Self.curBit, #7

	// done?
	sub r8,r8,#1
	qbbs _send_led_exitloop,r8,#15

	// fetch new byte
	lbbo Self.bits, r9, 0, 1
	add r9,r9,#1

	ldi Self.curBit,#7  // bit-counter back to start.
  _send_led__no_new_byte:

	// wait to start.
	mov r0, Self.cyc_next
	jal r24, PRU0_timer_wait_until
	// bit line high.
#ifdef NEG_LOGIC_OUT
	clr r30, r10.b0
#else
	set r30, r10.b0
#endif

	// check bit and decide if short or long
	mov r0, Self.cyc_next
	add r0,r0,Self.level0
	qbbc _send_led__shortbit, Self.bits, Self.curBit
	sub r0,r0,Self.level0
	add r0,r0,Self.level1
  _send_led__shortbit:
	jal r24, PRU0_timer_wait_until
	// bit line low.
#ifdef NEG_LOGIC_OUT
	set r30, r10.b0
#else
	clr r30, r10.b0
#endif

	// move to next bit.
	sub Self.curBit,Self.curBit,#1


	add Self.cyc_next,Self.cyc_next,#250

	jmp _send_led_loop


_send_led_exitloop:

	// now, wait about 50us. which is 10000
	mov r0, Self.cyc_next
	ldi r1,#10000
	add r0,r0,r1
	jal r24, PRU0_timer_wait_until

	sub Self.stack, Self.stack, #4+12
	lbbo r8, Self.stack, 4, 12
	lbbo r24, Self.stack, 0, 4
	jmp r24


