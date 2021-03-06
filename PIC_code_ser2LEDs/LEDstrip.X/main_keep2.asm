
;s5=serial.Serial(port="COM5",baudrate=800000,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_TWO,timeout=None,xonxoff=False,rtscts=False,writeTimeout=None,dsrdtr=False,interCharTimeout=None)

; config:
; RX/TX on usual port B1/B2 (pins 7,8)
; LED data out: port A0 (pin 17)
; baud select jumper: port B4/B5 (pins 9,10)

INDF0   = 0x000
INDF1   = 0x001
STATUS  = 0x003
FSR0L   = 0x004
FSR0H   = 0x005
FSR1L   = 0x006
FSR1H   = 0x007
BSR     = 0x008
WREG    = 0x009
PCLATH  = 0x00A
INTCON  = 0x00B
PORTA   = 0x00C
PORTB   = 0x00D
PIR1    = 0x011
PIR3    = 0x013
TMR1L   = 0x016
TMR1H   = 0x017
T1CON   = 0x018
T1GCON  = 0x019
TMR2    = 0x01A
PR2     = 0x01B
T2CON   = 0x01C
TRISA   = 0x08C
TRISB   = 0x08D
PIE1    = 0x091
PIE3    = 0x093
OPTION_REG = 0x095
OSCCON  = 0x099
LATA    = 0x10C
LATB    = 0x10D
ANSELA  = 0x18C
ANSELB  = 0x18D
RCREG   = 0x199
TXREG   = 0x19A
SPBRGL  = 0x19B
SPBRGH  = 0x19C
RCSTA   = 0x19D
TXSTA   = 0x19E
BAUDCON = 0x19F
WPUA    = 0x20C
WPUB    = 0x20D
IOCBP   = 0x394
IOCBN   = 0x395
TMR4    = 0x415
PR4     = 0x416
T4CON   = 0x417
TMR6    = 0x41C
PR6     = 0x41D
T6CON   = 0x41E
FSR0L_SHAD = 0xFE8
FSR0H_SHAD = 0xFE9
FSR1L_SHAD = 0xFEA
FSR1H_SHAD = 0xFEB

; PIC16F1847 Configuration Bit Settings
#include "p16F1847.inc"


; CONFIG1
; __config 0xEFC4
 __CONFIG _CONFIG1, _FOSC_INTOSC & _WDTE_OFF & _PWRTE_ON & _MCLRE_ON & _CP_OFF & _CPD_OFF & _BOREN_ON & _CLKOUTEN_OFF & _IESO_OFF & _FCMEN_ON
; CONFIG2
; __config 0xDFFF
 __CONFIG _CONFIG2, _WRT_OFF & _PLLEN_ON & _STVREN_ON & _BORV_LO & _LVP_OFF


ml_temp          = 0x70
ml_count         = 0x71     ; used to count while clocking out
ml_countH        = 0x72     ; high for ml_count
ml_countSequence = 0x73     ; used to count the match-sequence terminating the serial input.
ml_timeCount     = 0x74
ml_nextCount     = 0x75     ; value to match against ml_timeCount for next output.
ml_ledSequenceCount = 0x76
ml_byte0         = 0x77
ml_byte1         = 0x78
ml_byte0flag     = 0x79
ml_txCount       = 0x7A
;config bits: internal osc.


portA_pin = 0
portB_led   = 0
portB_powerJmp = 3
portB_baudsel0 = 4
portB_baudsel1 = 5
portB_TX = 2

buffer = 0x2000  ; max size 1008 bytes (all bank-mem) Beginning must be multiple of 0x100
bufferEnd = 0x2300  ; End. Must be multiple of 6 bytes. And of 256... because of buffer-end-check for serial input.


	org 0
	goto skipToSetup

	org 4
	retfie

skipToSetup:
	; oscillator setup ..... To get 32MHz internal, FOSC=100 (INTOSC), SCS=00 (source=INTOSC), IRCF=1110 (8MHz), SPLLEN=1 (PLLEN)
	movlw 0xF0	; PLL on, int osc 8MHz, clockselect by config.
	banksel OSCCON
	movwf OSCCON
	banksel 0

	movlw 0xC8
pauseOsc:
	nop
	nop
	decfsz WREG,0
	bra pauseOsc

    ; clear buffer
	movlw low bufferEnd
	movwf FSR0L
	movlw high bufferEnd
	movwf FSR0H
clrlop:
	movlw 0
	movwi --FSR0
	movwi --FSR0
	movwi --FSR0
	movf FSR0L,0
	btfss STATUS,Z
	bra clrlop
	movf FSR0H,0
	xorlw high buffer
	btfss STATUS,Z
	bra clrlop



	; port setup
	banksel ANSELA
	clrf ANSELA
	clrf ANSELB
	banksel WPUA
	movlw 0xFF
	movwf WPUA
	movwf WPUB
	banksel LATA
	bcf LATA,portA_pin
	bcf LATB,portB_led
	banksel TRISA
	movlw 0xFF-(1<<portA_pin)
	movwf TRISA
	movlw 0xFF-(1<<portB_TX)
	movwf TRISB
	banksel 0


	; UART BAUD rate setup. First set up for 500k.
	; formula for baudrate value:
	;  32e6/(16*500000)-1
	; 500kBaud @ 32MHz: 3
	banksel BAUDCON
	movlw 0x40
	movwf BAUDCON		; RCIDL (BRG16=0)
	banksel TXSTA
	bsf TXSTA,2 ; BRGH
	banksel SPBRGL
	movlw 0x03
	movwf SPBRGL
	movlw 0x00
	movwf SPBRGH
	banksel 0
	; high-bit
	btfss PORTB,portB_baudsel1
	bra lowSpeed
	; is high. Check if reducing to 250k
	btfsc PORTB,portB_baudsel0
	bra baudDone
	; reduce to 250k
	banksel SPBRGL
	movlw 0x07
	movwf SPBRGL
	banksel 0
	bra baudDone
lowSpeed:
	; low-speeds. set BRG16 bit to get moreprecision with these odd clock rates
	banksel BAUDCON
	bsf BAUDCON,3		; BRG16
	; and set to 115.2 kBaud.
	banksel SPBRGL
	movlw 0x44
	movwf SPBRGL
	banksel 0
	btfsc PORTB,portB_baudsel0
	bra baudDone
	; reduce to 57600
	banksel SPBRGL
	movlw 0x8A
	movwf SPBRGL
	banksel 0
baudDone:

	; UART setup (no interrupts!)
	banksel TXSTA
	bcf TXSTA,4	; SYNC
	bsf TXSTA,5	; TXEN (go)
	banksel RCSTA
	bsf RCSTA,7	; SPEN

	; UART RX setup.
	banksel RCSTA
	bcf RCSTA,6 ; RX9
	bcf RCSTA,3 ; ADDEN
	bsf RCSTA,4 ; CREN (go!)
	banksel PIE1
	bcf PIE1,5	; without intrr

	; timer4 is the time-clock. always running without ints.  64*10*250=160000 -> 50 Hz (@8MHz).
	; value is polled from mainloop. It wraps slow enough for this.
	; timer 4 period is 160000 cycles.
	banksel TMR4
	movlw 0xF9	; 250-1
	movwf PR4
	movlw 0x4F  ; prescale=64, enable, postscale=1:10
	movwf T4CON
	clrf ml_timeCount
	banksel PIE3
	bcf PIE3,1  ; disable int


	clrf ml_nextCount

	clrf ml_ledSequenceCount

	clrf ml_txCount

	banksel 0
	movlw low buffer
	movwf FSR1L
	movlw high buffer
	movwf FSR1H


;debugtestloop:
;	banksel PIR1
;	btfss PIR1,5
;	bra debugtestloop
;	banksel RCREG
;	movf RCREG,0
;	banksel 0
;	movwf ml_temp
;	incf ml_count,1
;	movlw 3
;	andwf ml_count
;	btfsc STATUS,Z
;	incf ml_temp,1
;	movf ml_temp,0
;	banksel TXREG
;	movwf TXREG
;	banksel 0
;	bra debugtestloop


	; just testing for simulator.
	movlw low buffer
	movwf FSR1L
	movlw high buffer
	movwf FSR1H
	movlw '#'
	movwi FSR1++
	movlw '#'
	movwi FSR1++
	call checkSeqF1
	movlw 'S'
	movwi FSR1++
	movlw 'E'
	movwi FSR1++
	movlw 'Q'
	movwi FSR1++
	movlw '-'
	movwi FSR1++
	movlw 'E'
	movwi FSR1++
	movlw 'N'
	movwi FSR1++
	movlw 'D'
	movwi FSR1++
	call checkSeqF1
	movlw '.'
	movwi FSR1++
	call checkSeqF1



	goto begin



sendAll:
	banksel 0
	movlw low buffer
	movwf FSR0L
	movwf FSR1L
	movlw high buffer
	movwf FSR0H
	movwf FSR1H

	; check timer before
	btfss PIR3,1    ; TMR4 int flag?
	bra noTmr4_1
	bcf PIR3,1
	incf ml_timeCount,1
noTmr4_1:
	movlw 0xD0  ;;;   all 240: 0xD0     24LEDs was 0x48
	movwf ml_count
	movlw 0x02  ;;;   all 240: 0x02     24LEDs was 0
	movwf ml_countH
	banksel LATA
loop:		; one byte is 8*10 cycles. Every two full byte-cycles, RX can have a new input byte (if one stop-bit)
	bsf LATA,portA_pin		; bit #7
	moviw FSR0++
	btfss WREG,7    ; should be ml_temp,7  but data is not yet in ml_temp ...
	bcf LATA,portA_pin
	movwf ml_temp
	nop
	bcf LATA,portA_pin
	  banksel PIR1
	  movf PIR1,0
	  banksel LATA
	bsf LATA,portA_pin		; bit #6
	nop
	btfss ml_temp,6
	bcf LATA,portA_pin
	nop
	nop
	bcf LATA,portA_pin
	  btfsc WREG,5 ; RCIF of PIR1
	  bra pathWithRX
	nop

 ; path without RX
	bsf LATA,portA_pin		; bit #5
	nop
	btfss ml_temp,5
	bcf LATA,portA_pin
	nop
	nop
	bcf LATA,portA_pin
	nop
	nop
	nop
	bsf LATA,portA_pin		; bit #4
	nop
	btfss ml_temp,4
	bcf LATA,portA_pin
	nop
	nop
	bcf LATA,portA_pin
	nop
	  bra normalAgain


pathWithRX:
	bsf LATA,portA_pin		; bit #5
	nop
	btfss ml_temp,5
	bcf LATA,portA_pin
	nop
	nop
	bcf LATA,portA_pin
	  banksel RCREG
	  movf RCREG,0
	  banksel LATA
	bsf LATA,portA_pin		; bit #4
	  movwi FSR1++
	btfss ml_temp,4
	bcf LATA,portA_pin
	nop
	nop
	bcf LATA,portA_pin
	nop
	nop
	nop

normalAgain:
	bsf LATA,portA_pin		; bit #3
	nop
	btfss ml_temp,3
	bcf LATA,portA_pin
	nop
	nop
	bcf LATA,portA_pin
	nop
    nop
	nop
	bsf LATA,portA_pin		; bit #2
	nop
	btfss ml_temp,2
	bcf LATA,portA_pin
	nop
	  decf ml_count,1
	bcf LATA,portA_pin
	  incf ml_count,0
	  btfsc STATUS,Z
	  decf ml_countH,1
	bsf LATA,portA_pin		; bit #1
	nop
	btfss ml_temp,1
	bcf LATA,portA_pin
	nop
	nop
	bcf LATA,portA_pin
	  movf ml_count,0
	  iorwf ml_countH,0
	  movf STATUS,0
	bsf LATA,portA_pin		; bit #0
	nop
	btfss ml_temp,0
	bcf LATA,portA_pin
	nop
	nop
	bcf LATA,portA_pin
	  btfss WREG,Z
	  bra loop

    ; loop is done. one more pulse?
    nop
	bsf LATA,portA_pin		; bit #end
    ; total instructions between bsf and bcf:  2 + 4*n-1
    movlw 0x02
    movwf ml_temp
final1:
    nop
    decfsz ml_temp,1
    bra final1
	bcf LATA,portA_pin


	movlw low buffer
	xorwf FSR1L,0
	btfss STATUS,Z
	bra hadquickRX
	movlw high buffer
	xorwf FSR1H,0
	btfss STATUS,Z
	bra hadquickRX
	bra noquickRX
hadquickRX:
	call minRestTime
noquickRX:

	incf ml_nextCount,1
	incf ml_nextCount,1
	incf ml_nextCount,1
;;;	incf ml_nextCount,1

	

	; LED data stream is done. Keep receiving until having 192 bytes.
	; At this point, the input cannot have done the 192 bytes already.
	; keep receiving and wait for terminator sequence.
begin:
	banksel 0
	clrf ml_countSequence
waitrest:
	banksel 0
	btfss PIR3,1    ; TMR4 int flag?
	bra noTmr4_2
	bcf PIR3,1
	incf ml_timeCount,1
noTmr4_2:

	; check timeout?
	movf ml_nextCount,0
	xorwf ml_timeCount,0
	btfsc STATUS,Z
	bra timeOutWaitRX

	nop
	; check for UART output
	btfss PIR1,4	; TXIF
	bra noTX
	btfsc ml_txCount,6
	bra noTX
	movlw high getTXgreetMsgByte
	movwf PCLATH
	movf ml_txCount,0
	call getTXgreetMsgByte
	clrf PCLATH
	banksel TXREG
	movwf TXREG
	banksel 0
	incf ml_txCount,1
noTX:

	; check for UART input.
	btfss PIR1,5	; RCIF
	bra waitrest
	; have a byte in the UART's input buffer.
	; first check timeout.

	call minRestTime

	; now get the byte from UART RX.
	banksel RCREG
	movf RCREG,0
	banksel 0
	movwi FSR1++	; check buffer overrun?
	; check buffer pointer
	movlw low bufferEnd
	subwf FSR1L,0
	movlw high bufferEnd
	subwf FSR1H,0
	btfsc STATUS,C
	moviw --FSR1	; decrease to stay at end.
	; check received byte
	call checkSeqF1
	movwf ml_temp
	addlw '0'
	movf ml_temp,0
	btfss STATUS,Z
	bra waitrest
	; sequence is there.

	movlw 8
	subwf FSR1L,1
	movlw 0
	subwfb FSR1H,1
	movwi FSR1++
	movwi FSR1++
	movwi FSR1++
	movwi FSR1++
	movwi FSR1++
	movwi FSR1++
	movwi FSR1++
	movwi FSR1++
	; send ack.
;	banksel TXREG
;	movlw 'A'
;	movwf TXREG	; this triggers UART hardware. Not waiting for completion.
	banksel 0

	; and go!
	goto sendAll

timeOutWaitRX:
	; timed out. do something here ourselves.
	movf ml_nextCount,0
	andlw 0x1F
	btfss STATUS,Z
	bra noToggleLED
	banksel TRISB
	movlw 1<<portB_led
	xorwf TRISB,1
	banksel 0
noToggleLED:
	; first, move up all data.

	banksel 0
	movlw low bufferEnd
	movwf FSR1L
	movlw high bufferEnd
	movwf FSR1H
	movlw low (bufferEnd-3)
	movwf FSR0L
	movlw high (bufferEnd-3)
	movwf FSR0H
copyLoop:
	moviw --FSR0
	movwi --FSR1
	moviw --FSR0
	movwi --FSR1
	moviw --FSR0
	movwi --FSR1
	movf FSR0L,0
	btfss STATUS,Z
	bra copyLoop
	movf FSR0H,0
	xorlw high buffer
	btfss STATUS,Z
	bra copyLoop
	; done with move.
	; insert new stuff.
	movf ml_ledSequenceCount,0
	movwf ml_temp
	movlw high sequenceG
	movwf PCLATH
	movf ml_temp,0
	call sequenceG
	movwf 0x20
	movf ml_temp,0
	call sequenceR
	movwf 0x21
	movf ml_temp,0
	call sequenceB
	movwf 0x22
	clrf PCLATH

	banksel 0
	btfss PORTB,portB_powerJmp
	bra isFullPwr
	rrf 0x20,0
	rrf WREG,0
	rrf WREG,0
	andlw 0x1F
	movwf 0x20
	rrf 0x21,0
	rrf WREG,0
	rrf WREG,0
	andlw 0x1F
	movwf 0x21
	rrf 0x22,0
	rrf WREG,0
	rrf WREG,0
	andlw 0x1F
	movwf 0x22
	;		movlw 0xff
	;		movwf 0x20
	;		movwf 0x21
	;		movwf 0x22
isFullPwr:


    incf ml_ledSequenceCount,1

	;banksel TXREG
	;movlw '.'
	;movwf TXREG	; this triggers hardware. Not waiting for completion.
    ; and go!
    goto sendAll




checkSeqF1:
	movlw low (buffer+8)
	subwf FSR1L,0
	movlw high (buffer+8)
	subwfb FSR1H,0
	btfss STATUS,C
	retlw 1	; too short
	movlw 8
	subwf FSR1L,1
	movlw 0
	subwfb FSR1H,1
	moviw FSR1++
	xorlw 'S'
	movwf ml_temp
	moviw FSR1++
	xorlw 'E'
	iorwf ml_temp,1
	moviw FSR1++
	xorlw 'Q'
	iorwf ml_temp,1
	moviw FSR1++
	xorlw '-'
	iorwf ml_temp,1
	moviw FSR1++
	xorlw 'E'
	iorwf ml_temp,1
	moviw FSR1++
	xorlw 'N'
	iorwf ml_temp,1
	moviw FSR1++
	xorlw 'D'
	iorwf ml_temp,1
	moviw FSR1++
	xorlw '.'
	iorwf ml_temp,1
	btfsc STATUS,Z
	retlw 0
	retlw 2


minRestTime:
	; (nextCount-timeCount)
	movf ml_timeCount,0
	subwf ml_nextCount,0
	andlw 0xF0
	btfss STATUS,Z
	return
	movlw 16
	addwf ml_timeCount,0
	movwf ml_nextCount
	return



take16bitColor:
	btfsc ml_byte0flag,0
	bra secondByteHiCol
	movwf ml_byte1
	bsf ml_byte0flag,0
	retlw 0
secondByteHiCol:
	movwf ml_byte0
	; extract high 5 bits as 'red'.
	rrf ml_byte1,0
	rrf WREG,0
	rrf WREG,0
	call gamma5
	movwi FSR1++
	; extract middle 6 bits as 'green'.
	lslf ml_byte0,0
	rlf ml_byte1,1
	lslf WREG,0
	rlf ml_byte1,1
	lslf WREG,0
	rlf ml_byte1,0
	call gamma6
	movwi FSR1++
	; extract low 5 bits as 'blue'.
	movf ml_byte0,0
	call gamma5
	movwi FSR1++
	retlw 1


	org 0x800

getTXgreetMsgByte:
	andlw 0x3F
	brw
;	dw 0x3420,0x3420,0x3420,0x340A,0x344C,0x3445,0x3444,0x3420,0x3473,0x3474,0x3472,0x3469,0x3470,0x342E,0x340A,0x3453
;	dw 0x3465,0x346E,0x3464,0x3420,0x3431,0x3436,0x342D,0x3462,0x3469,0x3474,0x342C,0x3420,0x3462,0x3469,0x3467,0x342D
;	dw 0x3465,0x346E,0x3464,0x3469,0x3461,0x346E,0x3420,0x3435,0x343A,0x3436,0x343A,0x3435,0x3420,0x3452,0x3447,0x3442
;	dw 0x3420,0x3464,0x3461,0x3474,0x3461,0x3420,0x346F,0x346E,0x3420,0x3455,0x3441,0x3452,0x3454,0x342E,0x340A,0x340A

	dw 0x3420,0x340A,0x340D,0x344C,0x3445,0x3444,0x3420,0x3473,0x3474,0x3472,0x3469,0x3470,0x342E,0x340A,0x340D,0x3453
	dw 0x3465,0x346E,0x3464,0x3420,0x3431,0x3436,0x342D,0x3462,0x3469,0x3474,0x342C,0x3420,0x3462,0x3469,0x3467,0x342D
	dw 0x3465,0x346E,0x3464,0x3469,0x3461,0x346E,0x3420,0x3435,0x343A,0x3436,0x343A,0x3435,0x3420,0x3452,0x3447,0x3442
	dw 0x3420,0x3464,0x3461,0x3474,0x3461,0x3420,0x346F,0x346E,0x3420,0x3455,0x3441,0x3452,0x3454,0x342E,0x340A,0x340D
;msg = " \n\rLED strip.\n\rSend 16-bit, big-endian 5:6:5 RGB data on UART.\n\r"
;len(msg)
;print "dw "+",".join( "0x%X"%(0x3400+ord(b)) for b in msg )


sequenceR:
	brw
	dw 0x3431,0x341F,0x3418,0x341F,0x3431,0x344B,0x3469,0x348B,0x34B0,0x34D7,0x34FF,0x34D7,0x34B0,0x348B,0x3469,0x344B
	dw 0x3431,0x341C,0x340C,0x3403,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400
	dw 0x3400,0x3401,0x3405,0x340B,0x3412,0x341C,0x3428,0x3435,0x3443,0x3452,0x3461,0x3452,0x3443,0x3435,0x3428,0x341C
	dw 0x3412,0x340E,0x3411,0x341D,0x3431,0x344B,0x3469,0x348B,0x34B0,0x34D7,0x34FF,0x34D7,0x34B0,0x348B,0x3469,0x344B
	dw 0x3431,0x341D,0x3410,0x340D,0x3411,0x341B,0x3426,0x3432,0x343F,0x344D,0x345C,0x344D,0x343F,0x3432,0x3426,0x341B
	dw 0x3411,0x340B,0x3409,0x340B,0x3412,0x341C,0x3427,0x3434,0x3442,0x3451,0x3460,0x3451,0x3442,0x3434,0x3427,0x341C
	dw 0x3412,0x340B,0x340B,0x340D,0x3416,0x3422,0x342F,0x343F,0x344F,0x3461,0x3473,0x3461,0x344F,0x343F,0x342F,0x3422
	dw 0x3416,0x340E,0x3410,0x3417,0x3427,0x343B,0x3453,0x346E,0x348C,0x34AB,0x34CA,0x34AB,0x348C,0x346E,0x3453,0x343B
	dw 0x3427,0x3417,0x340C,0x3408,0x340A,0x340F,0x3415,0x341C,0x3423,0x342B,0x3433,0x342B,0x3423,0x341C,0x3415,0x340F
	dw 0x340A,0x3406,0x3402,0x3401,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400
	dw 0x3400,0x3403,0x340B,0x3419,0x342B,0x3442,0x345D,0x347C,0x349C,0x34BF,0x34E2,0x34BF,0x349C,0x347C,0x345D,0x3442
	dw 0x342B,0x341B,0x3413,0x3416,0x3421,0x3433,0x3447,0x345E,0x3477,0x3492,0x34AD,0x3492,0x3477,0x345E,0x3447,0x3433
	dw 0x3421,0x3413,0x3408,0x3402,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400
	dw 0x3400,0x3402,0x3407,0x340F,0x341B,0x3429,0x343A,0x344C,0x3461,0x3476,0x348C,0x3476,0x3461,0x344C,0x343A,0x3429
	dw 0x341B,0x3412,0x3413,0x341E,0x3431,0x344B,0x3469,0x348B,0x34B0,0x34D7,0x34FF,0x34D7,0x34B0,0x348B,0x3469,0x344B
	dw 0x3431,0x341F,0x3418,0x341F,0x3431,0x344B,0x3469,0x348B,0x34B0,0x34D7,0x34FE,0x34D7,0x34B0,0x348B,0x3469,0x344B

sequenceG:
	brw
	dw 0x3407,0x3407,0x340E,0x341C,0x3431,0x344B,0x3469,0x348B,0x34B0,0x34D7,0x34FF,0x34D7,0x34B0,0x348B,0x3469,0x344B
	dw 0x3431,0x341E,0x3414,0x3414,0x341E,0x342D,0x3440,0x3455,0x346B,0x3483,0x349B,0x3483,0x346B,0x3455,0x3440,0x342D
	dw 0x341E,0x3411,0x3408,0x3402,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400
	dw 0x3400,0x3400,0x3401,0x3403,0x3404,0x3407,0x340A,0x340D,0x3410,0x3414,0x3417,0x3414,0x3410,0x340D,0x340A,0x3407
	dw 0x3404,0x3405,0x340B,0x3416,0x3427,0x343B,0x3453,0x346E,0x348B,0x34AA,0x34CA,0x34AA,0x348B,0x346E,0x3453,0x343B
	dw 0x3427,0x3416,0x340A,0x3402,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400
	dw 0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400
	dw 0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400
	dw 0x3400,0x3403,0x340C,0x341A,0x342E,0x3447,0x3464,0x3484,0x34A7,0x34CC,0x34F2,0x34CC,0x34A7,0x3484,0x3464,0x3447
	dw 0x342E,0x341B,0x3411,0x340E,0x3413,0x341E,0x342A,0x3437,0x3446,0x3455,0x3465,0x3455,0x3446,0x3437,0x342A,0x341E
	dw 0x3413,0x340B,0x3405,0x3401,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400
	dw 0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400
	dw 0x3400,0x3401,0x3402,0x3405,0x3409,0x340E,0x3414,0x341B,0x3422,0x3429,0x3431,0x3429,0x3422,0x341B,0x3414,0x340E
	dw 0x3409,0x3407,0x3409,0x3412,0x341D,0x342D,0x343F,0x3454,0x346A,0x3481,0x3499,0x3481,0x346A,0x3454,0x343F,0x342D
	dw 0x341D,0x3411,0x3408,0x3405,0x3405,0x3408,0x340B,0x340E,0x3412,0x3416,0x341A,0x3416,0x3412,0x340E,0x340B,0x3408
	dw 0x3405,0x3403,0x3403,0x3404,0x3407,0x340B,0x3410,0x3415,0x341B,0x3421,0x3427,0x3421,0x341B,0x3415,0x3410,0x340B

sequenceB:
	brw
	dw 0x3400,0x3403,0x340C,0x341C,0x3431,0x344B,0x3469,0x348B,0x34B0,0x34D7,0x34FF,0x34D7,0x34B0,0x348B,0x3469,0x344B
	dw 0x3431,0x341E,0x3413,0x3412,0x341A,0x3429,0x3439,0x344C,0x3460,0x3475,0x348A,0x3475,0x3460,0x344C,0x3439,0x3429
	dw 0x341A,0x3411,0x3411,0x3417,0x3426,0x343A,0x3451,0x346B,0x3488,0x34A6,0x34C5,0x34A6,0x3488,0x346B,0x3451,0x343A
	dw 0x3426,0x3415,0x340A,0x3402,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400
	dw 0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400
	dw 0x3400,0x3402,0x340A,0x3416,0x3426,0x343A,0x3451,0x346C,0x3489,0x34A7,0x34C6,0x34A7,0x3489,0x346C,0x3451,0x343A
	dw 0x3426,0x3418,0x3413,0x3415,0x3422,0x3434,0x344A,0x3462,0x347B,0x3497,0x34B3,0x3497,0x347B,0x3462,0x344A,0x3434
	dw 0x3422,0x3414,0x340D,0x340C,0x3411,0x341B,0x3425,0x3432,0x343F,0x344D,0x345B,0x344D,0x343F,0x3432,0x3425,0x341B
	dw 0x3411,0x340A,0x3404,0x3401,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400
	dw 0x3400,0x3402,0x3409,0x3415,0x3425,0x3438,0x344F,0x3469,0x3485,0x34A2,0x34C0,0x34A2,0x3485,0x3469,0x344F,0x3438
	dw 0x3425,0x3416,0x340C,0x3409,0x340D,0x3414,0x341C,0x3424,0x342E,0x3438,0x3443,0x3438,0x342E,0x3424,0x341C,0x3414
	dw 0x340D,0x3408,0x3409,0x340E,0x3417,0x3423,0x3432,0x3442,0x3453,0x3466,0x3478,0x3466,0x3453,0x3442,0x3432,0x3423
	dw 0x3417,0x3410,0x3412,0x341C,0x342F,0x3448,0x3465,0x3485,0x34A9,0x34CE,0x34F4,0x34CE,0x34A9,0x3485,0x3465,0x3448
	dw 0x342F,0x341B,0x340C,0x3403,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400
	dw 0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400
	dw 0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400,0x3400




gamma5:
	andlw 0x1F
	brw
	dw 0x3400,0x3401,0x3403,0x3406,0x340A,0x340E,0x3412,0x3418
	dw 0x341D,0x3423,0x342A,0x3431,0x3438,0x343F,0x3447,0x3450
	dw 0x3459,0x3462,0x346B,0x3475,0x347E,0x3489,0x3493,0x349E
	dw 0x34A9,0x34B5,0x34C0,0x34CC,0x34D9,0x34E5,0x34F2,0x34FF

gamma6:
	andlw 0x3F
	brw
	dw 0x3400,0x3400,0x3401,0x3402,0x3403,0x3404,0x3406,0x3408
	dw 0x3409,0x340B,0x340D,0x3410,0x3412,0x3414,0x3417,0x341A
	dw 0x341C,0x341F,0x3422,0x3425,0x3429,0x342C,0x342F,0x3433
	dw 0x3436,0x343A,0x343E,0x3442,0x3446,0x344A,0x344E,0x3452
	dw 0x3456,0x345B,0x345F,0x3464,0x3468,0x346D,0x3472,0x3476
	dw 0x347B,0x3480,0x3485,0x348A,0x3490,0x3495,0x349A,0x34A0
	dw 0x34A5,0x34AB,0x34B0,0x34B6,0x34BC,0x34C1,0x34C7,0x34CD
	dw 0x34D3,0x34D9,0x34DF,0x34E6,0x34EC,0x34F2,0x34F9,0x34FF

; python code used to generate tables above

;import math
;gamma = 1.6
;maxIn = 63
;A = 255/math.pow(maxIn,gamma)
;res=list()
;for i in xrange(maxIn+1):
;	res.append( int( A*math.pow(i,gamma) + 0.5 ) )
;
;for i in xrange(0,len(res),8):
;	part = res[i:i+8]
;	print 'dw ' + ','.join( '0x%02X'%(b+0x3400) for b in part )




    end


