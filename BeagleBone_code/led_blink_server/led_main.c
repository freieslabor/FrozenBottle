/*
 * PRU_memAccessPRUDataRam.c
*/

/*****************************************************************************
* PRU_memAccessPRUDataRam.c
*
* The PRU reads and stores values into the PRU Data RAM memory. PRU Data RAM
* memory has an address in both the local data memory map and global memory
* map. The example accesses the local Data RAM using both the local address
* through a register pointed base address and the global address pointed by
* entries in the constant table.
*
******************************************************************************/

#include <stdio.h>
#include <string.h>
#include <malloc.h>
#include <unistd.h>

// headers for network and UDP
#include <arpa/inet.h>
#include <sys/socket.h>
#include <errno.h>

#define UDP_PORT 8901
#define PRU_MEM_LEDS_START 0x0800
#define PRU_MEM_LEDS_END 0x1E00

#define LEDS_NUM (16*60)  // number of leds for idle-play
#define IDLE_BRIGHTNESS 32  // bright-value (PWM, not pre-gamma) for idle-loop.
#define LIMIT_AVG_BRIGHT 48

// PRU driver header file
#include <prussdrv.h>
#include <pruss_intc_mapping.h>

#define PRU0_CODE_FILE "./led0.bin"
#define PRU1_CODE_FILE "./led1.bin"

static void showHex(const void *adr,unsigned int baseadr,unsigned int num);
static void showHexL(const void *adr,unsigned int baseadr,unsigned int num);
static unsigned char *loadfile_malloc(const char *filename,unsigned int *out_size);
static void adjust_timeout(char to_lng);
static void correct_values(unsigned char *buffer,unsigned int bytes);
static void limit_power(unsigned char *vals,unsigned int num_leds,unsigned char avg_max_pwm);
static char readInt(const char *arg,int *out_value,int _min,int _max);


const char _led_tp[] = "a";


typedef struct
{
	unsigned char *pru0_ram;
//	void *pru1_ram;

	int udp_sock;

	char timeout_long;

} _self;

_self self;

/*
#!/usr/bin/python
import math
vals=list();gamma=1.95;num=256
for i in xrange(num):
 vals.append( max( int(255.0*math.pow(i/float(num-1),gamma)+0.5) , 0 ) )

for i in xrange(0,num,16):
 print ' '+','.join("0x%02X"%b for b in vals[i:i+16])
*/

static const unsigned char gamma[] = {
	0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x01,0x01,0x01,0x01,0x01,
	0x01,0x01,0x01,0x02,0x02,0x02,0x02,0x02,0x03,0x03,0x03,0x03,0x03,0x04,0x04,0x04,
	0x04,0x05,0x05,0x05,0x06,0x06,0x06,0x07,0x07,0x07,0x08,0x08,0x08,0x09,0x09,0x09,
	0x0A,0x0A,0x0B,0x0B,0x0B,0x0C,0x0C,0x0D,0x0D,0x0E,0x0E,0x0F,0x0F,0x10,0x10,0x11,
	0x11,0x12,0x12,0x13,0x13,0x14,0x14,0x15,0x16,0x16,0x17,0x17,0x18,0x19,0x19,0x1A,
	0x1B,0x1B,0x1C,0x1D,0x1D,0x1E,0x1F,0x1F,0x20,0x21,0x21,0x22,0x23,0x24,0x24,0x25,
	0x26,0x27,0x28,0x28,0x29,0x2A,0x2B,0x2C,0x2C,0x2D,0x2E,0x2F,0x30,0x31,0x31,0x32,
	0x33,0x34,0x35,0x36,0x37,0x38,0x39,0x3A,0x3B,0x3C,0x3D,0x3E,0x3F,0x3F,0x40,0x41,
	0x43,0x44,0x45,0x46,0x47,0x48,0x49,0x4A,0x4B,0x4C,0x4D,0x4E,0x4F,0x50,0x51,0x53,
	0x54,0x55,0x56,0x57,0x58,0x59,0x5B,0x5C,0x5D,0x5E,0x5F,0x61,0x62,0x63,0x64,0x66,
	0x67,0x68,0x69,0x6B,0x6C,0x6D,0x6E,0x70,0x71,0x72,0x74,0x75,0x76,0x78,0x79,0x7A,
	0x7C,0x7D,0x7F,0x80,0x81,0x83,0x84,0x86,0x87,0x88,0x8A,0x8B,0x8D,0x8E,0x90,0x91,
	0x93,0x94,0x96,0x97,0x99,0x9A,0x9C,0x9D,0x9F,0xA0,0xA2,0xA3,0xA5,0xA7,0xA8,0xAA,
	0xAB,0xAD,0xAF,0xB0,0xB2,0xB4,0xB5,0xB7,0xB8,0xBA,0xBC,0xBE,0xBF,0xC1,0xC3,0xC4,
	0xC6,0xC8,0xCA,0xCB,0xCD,0xCF,0xD1,0xD2,0xD4,0xD6,0xD8,0xD9,0xDB,0xDD,0xDF,0xE1,
	0xE3,0xE4,0xE6,0xE8,0xEA,0xEC,0xEE,0xF0,0xF2,0xF3,0xF5,0xF7,0xF9,0xFB,0xFD,0xFF
};

static unsigned char LEDSbuf[3*LEDS_NUM];

int main(int numargs,const char *const* args)
{
  unsigned int ret;
  unsigned int lop;
  void *eram;
  int i;
  int port;
  int level0,level1;
  unsigned char *buf;
  unsigned int size;
  const char *errtxt=0;

	memset( &self , 0 , sizeof(self) );
	self.udp_sock = -1;
	self.timeout_long = 33; // dummy. not 1, not 0

	port = UDP_PORT;
	level0 = 125-50;
	level1 = 125;

	printf("\n[led_main]\n");

	if(0)
	{
		// debug ugly try out the power-limiter
	  unsigned char data[8*3] = { 200,100,100 , 100,200,100 , 100,100,200 , 100,100,100 , 100,100,100 , 100,100,100 , 100,100,100 , 100,100,100 };
	  unsigned int i;
		limit_power(data,8,80);
		for(i=0;i<8;i++)
			printf("#%u  %3u/%3u/%3u\n",i,(unsigned int)(data[3*i+0]),(unsigned int)(data[3*i+1]),(unsigned int)(data[3*i+2]));
	}

	for(i=1;i<numargs;)
	{
	  const char *arg = args[i++];
		if(*arg=='-')
		{
			if(!strcasecmp(arg+1,"p"))
			{
				if(i>=numargs){errtxt="no value after 'p'";goto leave;}
				if(!readInt(args[i++],&port,32,65535))
					{errtxt="invalid value for p";goto leave;}
			}else if(!strcasecmp(arg+1,"l0"))
			{
				if(i>=numargs){errtxt="no value after 'l0'";goto leave;}
				if(!readInt(args[i++],&level0,10,190))
					{errtxt="invalid value for l0";goto leave;}
			}else if(!strcasecmp(arg+1,"l1"))
			{
				if(i>=numargs){errtxt="no value after 'l1'";goto leave;}
				if(!readInt(args[i++],&level1,10,190))
					{errtxt="invalid value for l1";goto leave;}
			}else{
				errtxt="invalid option. valid: -p,-l0,-l1.";
				goto leave;
			}
		}else{
			errtxt="unused parameter(s)";goto leave;
		}
	}

	if( level0+10 >= level1 )
		{errtxt="should have: L0+10 <= L1";goto leave;}

	// Initialize the PRU and driver
	prussdrv_init ();

	/* Open PRU Interrupt */
	ret = prussdrv_open(PRU_EVTOUT_0);
	if (ret)
	{
	    printf("prussdrv_open open failed\n");
	    return (ret);
	}

	// Get the interrupt initialized
	{
	  tpruss_intc_initdata idata = PRUSS_INTC_INITDATA;
		prussdrv_pruintc_init(&idata);
	}

	// setup stuff. reset PRU and prepare for loading.
	prussdrv_pru_reset(0);
	prussdrv_map_prumem(PRUSS0_PRU0_DATARAM, (void**)&(self.pru0_ram));

	// map ext-ram area
	prussdrv_map_extmem(&eram);
	printf("PRU ext-ram: %p\n",eram);

	// init LEDSbuf
	memset( LEDSbuf , sizeof(LEDSbuf) , IDLE_BRIGHTNESS );

	// clear, set levels.
	buf = (unsigned char*)malloc(0x01000);
	memset(buf,0,0x01000);
	buf[4] = (unsigned char)level0;
	buf[5] = (unsigned char)level1;
	prussdrv_pru_write_memory(PRUSS0_PRU0_DATARAM,0,(const unsigned int*)buf,0x01000);
	prussdrv_pru_write_memory(PRUSS0_PRU1_DATARAM,0,(const unsigned int*)buf,0x01000);
	free(buf);


	// load program to memory.
	buf = loadfile_malloc(PRU0_CODE_FILE,&size);
	if(!buf)
		{errtxt="Cannot load '" PRU0_CODE_FILE "'.";goto leave;}
	prussdrv_pru_write_memory(PRUSS0_PRU0_IRAM,0,(const unsigned int*)buf,size);
	free(buf);

#ifdef PRU1_CODE_FILE
	// load program for second PRU unit to memory.
	buf = loadfile_malloc(PRU1_CODE_FILE,&size);
	if(!buf)
		{errtxt="Cannot load '" PRU1_CODE_FILE "'.";goto leave;}
	prussdrv_pru_write_memory(PRUSS0_PRU1_IRAM,0,(const unsigned int*)buf,size);
	free(buf);
#endif


	// open UDP port
	self.udp_sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
	if(self.udp_sock<0)
		{errtxt="Error opening UDP port for receiving.";goto leave;}
	//bind socket to port and set opts
	{
	  struct sockaddr_in6 bindadr6;
	  struct sockaddr_in bindadr4;
	  struct timeval tv;
		memset( &bindadr6 , 0 , sizeof(bindadr6) );
		memset( &bindadr4 , 0 , sizeof(bindadr4) );
		bindadr6.sin6_port = htons(port);
		bindadr4.sin_port = htons(port);
		if( bind(self.udp_sock,(struct sockaddr*)&bindadr4,sizeof(bindadr4)) < 0 )
			{errtxt="Error binding UDP port";goto leave;}
		tv.tv_sec = 0;
		tv.tv_usec = 200000;
		setsockopt(self.udp_sock,SOL_SOCKET,SO_RCVTIMEO,(const char*)&tv,sizeof(tv));
	}



	// Start PRU unit #0.
	prussdrv_pru_enable_at(0, 0);



	// main loop


	// TODO: If hitting timeout, reduce timeout to 100ms. If having data, increase timeout to 2.5sec.


	for(lop=0;;lop++)   //for(lop=0;lop<10000;lop++)
	{
	  int ln;
	  socklen_t adrlen;
	  unsigned char pckbuf[10240];
	  struct sockaddr_in6 srcadr;


		memset( &srcadr , 0 , sizeof(srcadr) );
		adrlen = sizeof(srcadr);
		ln = recvfrom( self.udp_sock , pckbuf , sizeof(pckbuf) , MSG_TRUNC , (struct sockaddr*)&srcadr , &adrlen );
		if( ln==EAGAIN || ln==EWOULDBLOCK || ln==-1 )
		{
			// generate something here.
		  int i;
			memset( LEDSbuf , IDLE_BRIGHTNESS , 3*LEDS_NUM );

			i = lop%LEDS_NUM;
			LEDSbuf[3*i+0] = 140;
			LEDSbuf[3*i+1] = 120;
			LEDSbuf[3*i+2] = 30;

			ln = 3*LEDS_NUM;

			correct_values(LEDSbuf,LEDS_NUM);

			adjust_timeout(0);
		}else if(ln>=5)
		{
			if( ln > (3*LEDS_NUM) )
				ln = (3*LEDS_NUM);
			ln /= 3;

			memcpy( LEDSbuf , pckbuf , ln*3 );
			correct_values(LEDSbuf,ln);

			adjust_timeout(1);
		}

		// put in framebuffer
		if(ln>=3)
		{
			// simply dump into target memory. Clamp to maximum of 0x1E00 - 0x0800 bytes.
			limit_power(LEDSbuf,LEDS_NUM,LIMIT_AVG_BRIGHT);

//			if( ln > (PRU_MEM_LEDS_END-PRU_MEM_LEDS_START-2) )
//				ln = (PRU_MEM_LEDS_END-PRU_MEM_LEDS_START-2) ;

			// Do gamma-correct and byte-swap

			ln = 3*LEDS_NUM;
			memcpy( self.pru0_ram+PRU_MEM_LEDS_START+2 , LEDSbuf , ln );
			self.pru0_ram[PRU_MEM_LEDS_START+0] = (unsigned char)ln;
			self.pru0_ram[PRU_MEM_LEDS_START+1] = (unsigned char)(ln>>8);
		}
		// TODO: another else part to exit on error?

	}


	/* Wait until PRU0 has finished execution */
//	printf("\tINFO: Waiting for HALT command.\r\n");
//	prussdrv_pru_wait_event (PRU_EVTOUT_0);
//	printf("\tINFO: PRU completed transfer.\r\n");
//	prussdrv_pru_clear_event (PRU_EVTOUT_0, PRU0_ARM_INTERRUPT);

	usleep(100000);

	if(self.pru0_ram)
	{
		showHexL(self.pru0_ram,0,256);
		printf("\n");
		showHex(self.pru0_ram+0x800,0x800,128);
	}

leave:
	if(errtxt)
		fprintf(stderr,"Error: %s\n",errtxt);

	if(self.udp_sock)
	{
		close(self.udp_sock);
	}

	// Disable PRU and close memory mapping
	prussdrv_pru_disable(0);
	prussdrv_exit ();

	return (errtxt?5:0);
}



static void showHex(const void *adr,unsigned int baseadr,unsigned int num)
{
	while(num>0)
	{
	  unsigned int i;
		// one line
		printf("%08X |",(baseadr&~31));
		for(i=0;i<(baseadr&31);i++)
			printf("   ");
		for(;i<32&&num>0;i++){
			printf(" %02X",(unsigned int)(*((const unsigned char*)adr)));
			adr++;num--;
		}
		baseadr = (baseadr+32)&~31;
		printf("\n");
	}
}

static void showHexL(const void *adr,unsigned int baseadr,unsigned int num)
{
  const unsigned int *rd;
	rd = (const unsigned int*)adr;
	num = num>>2;
	while(num>0)
	{
	  unsigned int i;
		// one line
		printf("%08X |",(baseadr&~7)<<2);
		for(i=0;i<(baseadr&7);i++)
			printf("   ");
		for(;i<8&&num>0;i++){
			printf(" %08X",*rd);
			rd++;num--;
		}
		baseadr = (baseadr+8)&~7;
		printf("\n");
	}
}

static unsigned char *loadfile_malloc(const char *filename,unsigned int *out_size)
{
  FILE *f;
  unsigned char *res;
  unsigned int dr,size;

	f = fopen(filename,"rb");
	if(!f)return 0;
	fseek(f,0,SEEK_END);
	size = (unsigned int)ftell(f);
	fseek(f,0,SEEK_SET);

	if(size<=0){fclose(f);return 0;}

	res = (unsigned char*)malloc(size+1);
	if(!res){fclose(f);return 0;}

	dr = fread(res,1,size,f);
	fclose(f);

	if(dr<size)
		{free(res);return 0;}

	res[size] = 0;

	*out_size = size;
	return res;
}

static void adjust_timeout(char to_lng)
{
  struct timeval tv;

	if( self.timeout_long == (unsigned char)to_lng )
		return;
	self.timeout_long=to_lng;

	if(to_lng)
	{
		tv.tv_sec = 2;
		tv.tv_usec = 500000;
	}else{
		tv.tv_sec = 0;
		tv.tv_usec = 50000;
	}
	setsockopt(self.udp_sock,SOL_SOCKET,SO_RCVTIMEO,(const char*)&tv,sizeof(tv));
}

static void correct_values(unsigned char *buffer,unsigned int numleds)
{
  unsigned int i;
	for(i=0;i<numleds;i++)
	{
		unsigned char r,g,b;
		r=buffer[0];
		g=buffer[1];
		b=buffer[2];
		r = gamma[r];
		g = gamma[g];
		b = gamma[b];
		if( i>=sizeof(_led_tp) || _led_tp[i]!='b' )
		{
			// type 'a' is G-R-B
			*(buffer++)=g;
			*(buffer++)=r;
			*(buffer++)=b;
		}else{
			// type 'b' is B-R-G
			*(buffer++)=b;
			*(buffer++)=r;
			*(buffer++)=g;
		}
	}
}

// limits values in-place in input buffer
static void limit_power(unsigned char *vals,unsigned int num_leds,unsigned char avg_max_pwm)
{
  unsigned int sumC1,sumC2,sumC3;
  unsigned int pow,max;
  unsigned int fact;
  unsigned int i;
  unsigned char *p;
	// count sums
	sumC1=sumC2=sumC3=0;
	for( p=vals,i=0 ; i<num_leds ; i++ )
	{
		sumC1 += *(p++);
		sumC2 += *(p++);
		sumC3 += *(p++);
	}
	pow = sumC1+sumC2+sumC3;
	max = avg_max_pwm*3*num_leds;
	if( pow <= max )
		return;
	// is too high. need to throttle.
	// with 60*60 LEDs, and 3 parts, all 0xFF, value is still less than (1<<22).
	fact = (max<<8) / pow;
	// scale all.
	for( p=vals,i=0 ; i<num_leds ; i++ )
	{
		p[0] = (unsigned char)((fact*p[0])>>8);
		p[1] = (unsigned char)((fact*p[1])>>8);
		p[2] = (unsigned char)((fact*p[2])>>8);
		p += 3;
	}
}

static char readInt(const char *arg,int *out_value,int _min,int _max)
{
  int res=0;
  char neg = 0;
	while(*arg==' '||*arg==9)arg++;
	if(*arg=='-')
		{arg++;neg=1;}
	while(*arg>='0'&&*arg<='9')
	{
	  int t = 10*res+(unsigned int)(unsigned char)(*arg-'0');
		arg++;
		if(t<res)return 0;
		res=t;
	}
	while(*arg==' '||*arg==9||*arg==13)arg++;
	if(*arg&&*arg!=10)
		return 0;
	if(neg)res=-res;
	if( res<_min || res>_max )return 0;
	*out_value = res;
	return 1;
}


