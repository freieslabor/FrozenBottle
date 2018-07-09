#include "fix_values.h"
#include <math.h>
#include <string.h>

// mapping table for flipping blue- and green parts.
const char fix_map_GBswap[] = \
		"aaaaaababbaaaa" \
		"aabaababaaaaa" \
		"aabaaaabbaaaaa" \
		"aaaaaabaabbaa" \
		"bbbbabbabaaaaa" \
		"ababaaaababaa" \
		"babbbabaabbbaa" \
		"abbaaabbbbbab" \
		"baabaabaababaa" \
		"aabaabaababaa" \
		"aabaaaaaaaaaaa" \
		"abbbbaabaabbb" \
		"aabbbaaababbba" \
		"abbbaaabbbaaa" \
		"aaaaaaaaaaaaaa" \
		"aaaaaaaaaaaaa"
		;

unsigned int fix_map_GBswap__size = sizeof(fix_map_GBswap);

// mapping table for the four chroma variants the LEDs have.
// strangely enough, this does not correlate with the tp map.
const char fix_map_4types[] = \
		"gwgwwwbwlbwglw" \
		"lwblglgllgggw" \
		"glllgglbbgwgwg" \
		"wwwllgblglblw" \
		"blllwlbgllwlww" \
		"llllwlglbwbll" \
		"bllllgblwllbll" \
		"llllglblbllll" \
		"lwglwllwgbwlll" \
		"lwlgwlwgbwlll" \
		"lwlgwgwwggwglw" \
		"llllllwllglbl" \
		"wllbbggglllllg" \
		"gbbbgglbbllgg" \
		;

unsigned int fix_map_4types__size = sizeof(fix_map_GBswap);



static const float gamma_curve_cal_values[NUM_GAMMA_CURVES][3][2] =
{
  {{1.102,1.836},{1.156,1.942},{0.771,1.998}},// Zone 'l'
  {{1.008,1.913},{1.008,1.913},{1.008,1.913}},// Zone 'w'
  {{1.044,2.155},{0.965,1.888},{1.034,1.754}},// Zone 'g'
  {{1.316,1.915},{0.938,1.885},{0.771,1.946}},// Zone 'b'
};

char gamma4[NUM_GAMMA_CURVES][4][256];


unsigned char chr_2_gammano(char sym)
{
	switch(sym)
	{
	case 'w': return 1;
	case 'g': return 2;
	case 'b': return 3;
	default: return 0;
	}
}

void load_default_gammacurves()
{
  unsigned int zn,rgb,i;
	for(zn=0;zn<NUM_GAMMA_CURVES;zn++)
	{
		for(rgb=0;rgb<3;rgb++)
		{
		  float A,g;
			A = gamma_curve_cal_values[zn][rgb][0];
			g = gamma_curve_cal_values[zn][rgb][1];
#if 0
			// disable the custom adjusted curves...
			A = 1.0f;g = 1.9f;
#endif
			for(i=0;i<256;i++)
			{
			  int val;
				val = (int)( 255.0f*A*powf(i/255.0f,g) + 0.5f );
				if(val>255)val=255;
				gamma4[zn][rgb][i] = val;
			}
		}
	}
}

void correct_values(unsigned char *buffer,unsigned int numleds)
{
  unsigned int i;
  char sym;
// DEBUG
//  time_t tm;
//	tm = time(0);
// end DEBUG
	for(i=0;i<numleds;i++)
	{
		unsigned char r,g,b;
		r=buffer[0];
		g=buffer[1];
		b=buffer[2];
		sym = 'w';
		if( i<sizeof(fix_map_4types) )sym = fix_map_4types[i];
		sym = chr_2_gammano(sym);
		r = gamma4[(unsigned char)sym][0][r];
		g = gamma4[(unsigned char)sym][1][g];
		b = gamma4[(unsigned char)sym][2][b];
// DEBUG
//	tm = time(0);
//	if( (tm&2) && i<sizeof(fix_map_4types) && fix_map_4types[i]=='l' )
//		b=0;
// end DEBUG
		// check mapping table to swap blue- and green-parts.
		if( i>=sizeof(fix_map_GBswap) || fix_map_GBswap[i]!='b' )
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
void limit_power(unsigned char *vals,unsigned int num_leds,unsigned char avg_max_pwm)
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
