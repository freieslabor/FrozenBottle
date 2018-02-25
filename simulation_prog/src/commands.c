#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "commands.h"
#include "fix_values.h"
#include "read_text.h"




int process_command_packet(const char *cmd)
{
	// commands:
	skip_whitespace(&cmd,0);
	// GAMMA x num,num,num      x is one of l,w,b,g   , num is sequencce of numbers, new gamma curve.
	if( !strncmp(cmd,"GAMMA ",6) )
		return process_command_packet_gamma(cmd+6);


	return -1;
}

int process_command_packet_gamma(const char *cmd)
{
  unsigned char newgamma[0x100];
  char tabname;
  char rgb;
  unsigned int tab,rgbidx;
  char dummy[16];
  int i;

	// first is table name, and whitespace.
	tabname = *(cmd++);
	if( !tabname || tabname<'a' || tabname>'z' )return -1;
	tab = chr_2_gammano(tabname);

	skip_whitespace(&cmd,0);

	// second is channel (r,g,b) , and whitespace.
	rgb = *(cmd++);
	if( rgb!='r' && rgb!='g' && rgb!='b' )return -1;
	rgbidx=0;
	if(rgb=='g')rgbidx=1;
	else if(rgb=='b')rgbidx=2;

	skip_whitespace(&cmd,0);

	// here might be the word 'reset'.
	if( !strncmp(cmd,"reset",5) )
	{
		cmd+=5;
		skip_whitespace(&cmd,0);
		if(*cmd)return -1;
		// is a gamma reset command.
		printf("command reset gamma curve for %s %u.\n",dummy,tab);
		for(i=0;i<NUM_GAMMA_CURVES;i++)
			memcpy( gamma4[i][rgbidx] , gamma195 , 256 );
		return 0;
	}

	// now array of comma-seperated values.
	for( i=0 ; i<256 ; i++ )
	{
	  int32_t val;
		skip_whitespace(&cmd,0);
		if(!read_int(&cmd,&val))
			return -1;
		if(val>255||val<0)
			return -1;
		newgamma[i] = (unsigned char)val;
		skip_whitespace(&cmd,0);
		if(i<255)
		{
			if(*cmd!=',')return -1;
			cmd++;
		}
	}
	// here, string must end.
	skip_whitespace(&cmd,0);
	if(*cmd)return -1;
	dummy[0] = tabname;
	dummy[1] = 0;
	dummy[2] = rgb;
	dummy[3] = 0;
	printf("command set gamma curve for %s(%u) %s.\n",dummy,tab,dummy+2);
	for(i=0;i<256;i++)
		gamma4[tab][rgbidx][i] = newgamma[i];
	return 0;
}

