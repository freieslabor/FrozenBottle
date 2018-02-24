#include <stdio.h>
#ifdef WIN32
#include "SDL.h"
#else
#include "SDL2/SDL.h"
#endif
#include <math.h>
#include "hexfield.h"
#include "UDPrecv.h"
#include "catch_ctrlC.h"
#include "commands.h"
#include "fix_values.h"

#undef main

// Raster eines Hex, mit waagerechter Zeile
// Abstand dx: 1.0    Abstand zwei Reihen dy: sin(60) = 0.5*sqrt(3) = 0.8660254037844386
/*
import math
q=math.sin(math.pi/3.0)
for i in xrange(256):
 print "%3u   %.2f" % (i,i*q)
*/

#define GLASSES_FIRST_ROW 14
#define GLASSES_HIGH 14

//#define STEP_X 37
//#define STEP_Y 32
//#define WINDOW_GFX_WIDTH 1056
//#define WINDOW_GFX_HEIGHT 950

#define STEP_X 30
#define STEP_Y 26
#define WINDOW_GFX_WIDTH 850
#define WINDOW_GFX_HEIGHT 750

#define HEX_TEX_SIZE 128

/*
#!/usr/bin/python
import math
vals=list();gamma=1.0/1.95;num=256
for i in xrange(num):
 vals.append( max( int(65280.0*math.pow(i/float(num-1),gamma)+0.5) , 0 ) )

for i in xrange(0,num,16):
 print ' '+','.join("0x%04X"%b for b in vals[i:i+16])

*/
const unsigned short inverse_gamma195[] = {
	0x0000,0x0EE0,0x1539,0x1A21,0x1E48,0x21F4,0x2548,0x2859,0x2B35,0x2DE5,0x3072,0x32DF,0x3531,0x376C,0x3991,0x3BA4,
	0x3DA6,0x3F98,0x417C,0x4354,0x451F,0x46DF,0x4895,0x4A42,0x4BE5,0x4D80,0x4F13,0x509F,0x5224,0x53A1,0x5519,0x568A,
	0x57F6,0x595C,0x5ABD,0x5C19,0x5D70,0x5EC2,0x6010,0x615A,0x62A0,0x63E2,0x6520,0x665A,0x6791,0x68C4,0x69F4,0x6B21,
	0x6C4A,0x6D71,0x6E95,0x6FB6,0x70D4,0x71F0,0x7309,0x741F,0x7533,0x7644,0x7754,0x7861,0x796B,0x7A74,0x7B7B,0x7C7F,
	0x7D81,0x7E82,0x7F80,0x807D,0x8178,0x8271,0x8368,0x845E,0x8552,0x8644,0x8735,0x8824,0x8911,0x89FD,0x8AE8,0x8BD1,
	0x8CB9,0x8D9F,0x8E84,0x8F67,0x9049,0x912A,0x920A,0x92E8,0x93C5,0x94A1,0x957C,0x9655,0x972D,0x9805,0x98DB,0x99B0,
	0x9A83,0x9B56,0x9C28,0x9CF9,0x9DC8,0x9E97,0x9F65,0xA031,0xA0FD,0xA1C8,0xA291,0xA35A,0xA422,0xA4E9,0xA5B0,0xA675,
	0xA739,0xA7FD,0xA8C0,0xA982,0xAA43,0xAB03,0xABC2,0xAC81,0xAD3F,0xADFC,0xAEB9,0xAF74,0xB02F,0xB0E9,0xB1A3,0xB25B,
	0xB313,0xB3CB,0xB481,0xB537,0xB5ED,0xB6A1,0xB755,0xB808,0xB8BB,0xB96D,0xBA1E,0xBACF,0xBB7F,0xBC2F,0xBCDE,0xBD8C,
	0xBE3A,0xBEE7,0xBF94,0xC03F,0xC0EB,0xC196,0xC240,0xC2EA,0xC393,0xC43C,0xC4E4,0xC58B,0xC632,0xC6D9,0xC77F,0xC824,
	0xC8C9,0xC96E,0xCA12,0xCAB5,0xCB58,0xCBFB,0xCC9D,0xCD3F,0xCDE0,0xCE80,0xCF21,0xCFC0,0xD060,0xD0FE,0xD19D,0xD23B,
	0xD2D8,0xD375,0xD412,0xD4AE,0xD54A,0xD5E5,0xD680,0xD71B,0xD7B5,0xD84E,0xD8E8,0xD981,0xDA19,0xDAB1,0xDB49,0xDBE0,
	0xDC77,0xDD0E,0xDDA4,0xDE3A,0xDECF,0xDF64,0xDFF9,0xE08D,0xE121,0xE1B5,0xE248,0xE2DB,0xE36D,0xE400,0xE491,0xE523,
	0xE5B4,0xE645,0xE6D5,0xE765,0xE7F5,0xE885,0xE914,0xE9A3,0xEA31,0xEABF,0xEB4D,0xEBDB,0xEC68,0xECF5,0xED82,0xEE0E,
	0xEE9A,0xEF26,0xEFB1,0xF03C,0xF0C7,0xF151,0xF1DC,0xF265,0xF2EF,0xF378,0xF401,0xF48A,0xF513,0xF59B,0xF623,0xF6AA,
	0xF732,0xF7B9,0xF840,0xF8C6,0xF94C,0xF9D2,0xFA58,0xFADE,0xFB63,0xFBE8,0xFC6C,0xFCF1,0xFD75,0xFDF9,0xFE7D,0xFF00
};



HexArray field;

void process_UDP_data( unsigned char *input_buffer , unsigned int input_data );
void process_mouse_click(int sx,int sy);
void draw( SDL_Renderer *rend , unsigned int frameNo );
bool draw_a_hex( SDL_Texture *tex , float r1 , float r2 );
bool get_cell_screen_coord(unsigned int seq_idx,int *out_w,int *out_h,unsigned int *out_color);
void ctrl_c_func(void *ctx);

/// program main function
int main(int argc, char* argv[])
{
  int res;
  bool sdl_started;
  SDL_Window *wnd;
  SDL_Renderer *rend;
  const char *errtxt=0;
  unsigned char input_buffer[10240+4]; // +4 to allow to null-terminate commands-packets.
  unsigned int no_input_count;
  unsigned int frameNo;
  bool running;

	errtxt=0;
	wnd=0;
	rend=0;
	sdl_started=false;

	if(!UDP_setup())
	{
		errtxt="Cannot setup UDP listen socket";
		goto leave;
	}


	// for full setup
	field.setup_square( GLASSES_FIRST_ROW , GLASSES_HIGH , false , false , false , true );


	res = SDL_Init( SDL_INIT_TIMER | SDL_INIT_VIDEO | SDL_INIT_EVENTS );
	if(res!=0)
		{errtxt="error initializing SDL lib.";goto leave;}
	sdl_started=true;

	wnd = SDL_CreateWindow(
			"hexstack",
			SDL_WINDOWPOS_UNDEFINED,SDL_WINDOWPOS_UNDEFINED,
			WINDOW_GFX_WIDTH,WINDOW_GFX_HEIGHT,
			SDL_WINDOW_RESIZABLE
	);
	if(!wnd)
		{errtxt="Error creating window";goto leave;}

	rend = SDL_CreateRenderer( wnd , -1 , SDL_RENDERER_TARGETTEXTURE );
	if(!rend)
		{errtxt="Cannot init SDL renderer";goto leave;}


	no_input_count=0;
	frameNo = 0;
	running = true;

	CtrlC_handler_hook(ctrl_c_func,&running);

	load_default_gammacurves();

	while(running)
	{
	  SDL_Event e;
	  unsigned int input_data;
		while( SDL_PollEvent( &e ) != 0 )
		{
			//User requests quit
			if( e.type == SDL_QUIT )
				{errtxt=0;goto leave;}
			if( e.type == SDL_MOUSEBUTTONDOWN )
				{process_mouse_click(e.button.x,e.button.y);}
		}
		if(UDP_wait( input_buffer , &input_data , 100 ))
		{
			input_buffer[input_data] = 0;
			process_UDP_data( input_buffer , input_data );
			no_input_count=0;
		}else{
			no_input_count++;
			if(!(no_input_count&15))
			{
			  unsigned int color = 0;
				if(no_input_count&16)
					color = 0x888888ul;
				for(unsigned int t=0u;;t++)
					if(!field.set_sequence_color(t,color))
						break;
			}
		}
		draw(rend,frameNo);
		SDL_RenderPresent( rend );
		frameNo++;
	}



//	SDL_Delay(1000);


leave:
	printf("exit\n");

	CtrlC_handler_unhook();

	if(sdl_started)
		SDL_Quit();
	UDP_halt();
	return (errtxt?1:0);
}

/// This is called from mainloop whenever there is data from UDP reception. It is placed in the color-data of the field.
void process_UDP_data( unsigned char *input_buffer , unsigned int input_data )
{
  unsigned int i,numl;

	if( input_data>=16 && !memcmp(input_buffer,COMMAND_PCK_PREFIX,16) )
	{
		// is a command, not RGB data.
		process_command_packet((const char*)(input_buffer+16));
	}

	numl = input_data/3;
	if(numl<1)return;

	// filter/process values (gamma, channel swap, ...)
	correct_values(input_buffer,numl);

	for( i=0 ; i<numl ; i++ )
	{
	  unsigned int r,g,b;
		if( i>=fix_map_GBswap__size || fix_map_GBswap[i]!='b' )
		{
			// type 'a' is G-R-B
			g = *(input_buffer++);
			r = *(input_buffer++);
			b = *(input_buffer++);
		}else{
			// type 'b' is B-R-G
			b = *(input_buffer++);
			r = *(input_buffer++);
			g = *(input_buffer++);
		}
		r = inverse_gamma195[r];
		g = inverse_gamma195[g];
		b = inverse_gamma195[b];

		// ..... falsify to simulate wrong colors??

		r = (r+0x80)>>8;
		g = (g+0x80)>>8;
		b = (b+0x80)>>8;

		if(!field.set_sequence_color( i , (r)+(g<<8)+(b<<16) ))
			break;
	}
}

/// called on mouse click. Find nearest cell and display current color value.
void process_mouse_click(int sx,int sy)
{
  int best_dist;
  unsigned int best_color;
  unsigned int best_seq;
	best_dist=0x7FFFFFFF;
	best_color = 0;
	best_seq = ~0;
	for( unsigned int t=0 ; ; t++ )
	{
	  int x,y;
	  unsigned int col;
	  int dist;
		if(!get_cell_screen_coord(t,&x,&y,&col))
			break;
		x-=sx;y-=sy;
		dist = x*x+y*y;
		if( t==0 || dist<best_dist )
		{
			best_dist=dist;
			best_color=col;
			best_seq=t;
		}
	}
	if( best_seq != (unsigned int)(~0) )
	{
	  unsigned int r,g,b;
		r = (best_color)&0xFF;
		g = (best_color>>8)&0xFF;
		b = (best_color>>16)&0xFF;
		printf("  cell #%u   R=0x%02X G=0x%02X B=0x%02X \n",best_seq,r,g,b);
	}
}

/// called from mainloop to render the graphics.
void draw( SDL_Renderer *rend , unsigned int frameNo )
{
//  Sint16 px[8],py[8];
  static SDL_Texture *otex=0;
  SDL_Rect rc;
	if(!otex)
	{
		otex = SDL_CreateTexture( rend , SDL_PIXELFORMAT_RGBA8888 , SDL_TEXTUREACCESS_STREAMING , HEX_TEX_SIZE , HEX_TEX_SIZE );
		if(!otex)return;
		if(!draw_a_hex(otex,0.90f*(float)STEP_X,0.95f*(float)STEP_X))
			return;
	}
	SDL_RenderSetScale( rend , 1.0f , 1.0f );	// set to windowSize/logicalSize

	SDL_SetRenderDrawColor( rend , 68 , 68 , 68 , 255 );
	SDL_RenderClear( rend );

	SDL_SetRenderDrawColor( rend , 200 , 200 , 200 , 255 );

//	SDL_Texture *orgTex = SDL_GetRenderTarget(rend);
//	SDL_SetRenderTarget( rend , otex );
//	SDL_SetRenderTarget( rend , orgTex );


	SDL_SetTextureBlendMode( otex , SDL_BLENDMODE_BLEND );
	rc.w = HEX_TEX_SIZE;
	rc.h = HEX_TEX_SIZE;

	for( unsigned int t=0 ; ; t++ )
	{
	  int x,y;
	  unsigned int col;
		if(!get_cell_screen_coord(t,&x,&y,&col))
			break;
		rc.x = x-(HEX_TEX_SIZE>>1);
		rc.y = y-(HEX_TEX_SIZE>>1);
		SDL_SetTextureColorMod(otex,(col)&0xFF,(col>>8)&0xFF,(col>>16)&0xFF);
		SDL_RenderCopy( rend , otex , 0 , &rc );
	}

//	SDL_RenderDrawLine( rend , 0,0 , (frameNo%30)*10,300 );

}

/// Draw a single hex pixel-wise to a texture for later blitting. Done only once.
bool draw_a_hex( SDL_Texture *tex , float r1 , float r2 )
{
  int w,h,acc;
  float vx[6],vy[6];
  Uint32 tForm;
  void *pix;
  int pitch;
  unsigned int mulbits,addbits;
  float mulfac;
	SDL_QueryTexture( tex , &tForm , &acc , &w , &h );
	switch(tForm)
	{
	case SDL_PIXELFORMAT_ABGR4444:
	case SDL_PIXELFORMAT_ARGB4444:
		mulfac=15.0;mulbits=0x1000;addbits=0x0FFF;break;
	case SDL_PIXELFORMAT_RGBA4444:
	case SDL_PIXELFORMAT_BGRA4444:
		mulfac=15.0;mulbits=0x0001;addbits=0xFFF0;break;
	case SDL_PIXELFORMAT_ARGB8888:
	case SDL_PIXELFORMAT_ABGR8888:
		mulfac=255.0;mulbits=0x01000000;addbits=0x00FFFFFF;break;
	case SDL_PIXELFORMAT_RGBA8888:
	case SDL_PIXELFORMAT_BGRA8888:
		mulfac=255.0;mulbits=0x01;addbits=0xFFFFFF00;break;
	default:
		return false;
	}
	if(SDL_LockTexture(tex,0,&pix,&pitch))
		return false;

	for(unsigned int t=0;t<6;t++)
	{
	  float ang = (float)t;
		ang *= 3.14159265359f/3.0f;
		vx[t] = cosf(ang);
		vy[t] = sinf(ang);
	}

  float hw=0.5f*w;
  float hh=0.5f*h;
	for(unsigned int y=0;(int)y<h;y++)
	{
	  unsigned int *pp = (unsigned int*)pix;
	  float fy = y-hh;
		for(unsigned int x=0;(int)x<w;x++)
		{
		  float fx = x-hw;
		  float fout = 0.0f;
			for(unsigned int t=0;t<6;t++)
			{
			  float tmp = fx*vx[t]+fy*vy[t];
				if( tmp>fout )fout=tmp;
			}
			fout = 1.0f - (fout-r1)/(r2-r1);
			if(fout<0.0f)fout=0.0f;
			if(fout>1.0f)fout=1.0f;
		  int mul = (int)(fout*mulfac+0.5f);
			*(pp++) = mulbits*mul + addbits ;
		}
		pix = ((char*)pix)+pitch;
	}


	SDL_UnlockTexture(tex);
	return true;
}

/// call the get_sequence_item() function, but transform output coords to screen-pixel coords.
bool get_cell_screen_coord(unsigned int seq_idx,int *out_w,int *out_h,unsigned int *out_color)
{
  unsigned int col;
  int w,h;
	if(!field.get_sequence_item(seq_idx,&w,&h,&col))
		return false;
	w = STEP_X + (STEP_X>>3) + w*STEP_X;
	h = WINDOW_GFX_HEIGHT - STEP_Y - (STEP_Y>>2) - h*STEP_Y;
	*out_w = w;
	*out_h = h;
	if(out_color)
		*out_color = col;
	return true;
}

/// handler which is called when user hits Ctrl-C. Just sets the boolean pointed to by context to false.
void ctrl_c_func(void *ctx)
{
  bool *runvar;
	runvar = (bool*)ctx;
	*runvar = false;
}
