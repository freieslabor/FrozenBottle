#include <malloc.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "commands.h"
#include "fix_values.h"

// headers for network and UDP
#include <arpa/inet.h>
#include <sys/socket.h>
#include <errno.h>

#define UDP_PORT 8901
#define PRU_MEM_LEDS_START 0x0800
#define PRU_MEM_LEDS_END 0x1E00

#define LEDS_NUM (7*(13+14))  // number of leds for idle-play
#define IDLE_BRIGHTNESS 32  // bright-value (PWM, not pre-gamma) for idle-loop.
#define LIMIT_AVG_BRIGHT 255 // 48

// PRU driver header file
#include <prussdrv.h>
#include <pruss_intc_mapping.h>

#define PRU0_CODE_FILE "./led0.bin"
#define PRU1_CODE_FILE "./led1.bin"

static void showHex(const void *adr,unsigned int baseadr,unsigned int num);
static void showHexL(const void *adr,unsigned int baseadr,unsigned int num);
static unsigned char *loadfile_malloc(const char *filename,unsigned int *out_size);
static void adjust_timeout(char to_lng);
static char readInt(const char *arg,int *out_value,int _min,int _max);


#define MAX_PACK_SIZE 10240



typedef struct
{
	unsigned char *pru0_ram;
//	void *pru1_ram;

	int udp_sock;

	char timeout_long;

} _self;

_self self;



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

	// DEBUG
//	process_command_packet("GAMMA w 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255");

	memset( &self , 0 , sizeof(self) );
	load_default_gammacurves();

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
	  unsigned char pckbuf[MAX_PACK_SIZE+4];
	  struct sockaddr_in6 srcadr;


		memset( &srcadr , 0 , sizeof(srcadr) );
		adrlen = sizeof(srcadr);
		ln = recvfrom( self.udp_sock , pckbuf , MAX_PACK_SIZE , MSG_TRUNC , (struct sockaddr*)&srcadr , &adrlen );
		if( ln==EAGAIN || ln==EWOULDBLOCK || ln==-1 )
		{
			// no data. generate idle-animation here.
		  int i;
			memset( LEDSbuf , IDLE_BRIGHTNESS , 3*LEDS_NUM );

			i = lop%LEDS_NUM;
			LEDSbuf[3*i+0] = 140;
			LEDSbuf[3*i+1] = 120;
			LEDSbuf[3*i+2] = 30;

			ln = 3*LEDS_NUM;

			correct_values(LEDSbuf,LEDS_NUM);

			adjust_timeout(0);
		}else if( ln>=16 && !memcmp(pckbuf,COMMAND_PCK_PREFIX,16) )
		{
			// command-packet
			pckbuf[ln] = 0;	// null-terminate string.
			process_command_packet((const char*)pckbuf+16);
		}else if(ln>=5)
		{
			// is a packet of color-information
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
