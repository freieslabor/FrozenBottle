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

#undef main

// Raster eines Hex, mit waagerechter Zeile
// Abstand dx: 1.0    Abstand zwei Reihen dy: sin(60) = 0.5*sqrt(3) = 0.8660254037844386
/*
import math
q=math.sin(math.pi/3.0)
for i in xrange(256):
 print "%3u   %.2f" % (i,i*q)
*/

#define STEP_X 37
#define STEP_Y 32

#define GLASSES_FIRST_ROW 14
#define GLASSES_HIGH 7

#define HEX_TEX_SIZE 128

//#define WINDOW_GFX_WIDTH 1158 // for full setup
//#define WINDOW_GFX_HEIGHT 600
#define WINDOW_GFX_WIDTH 800  // for temporary 50-glass setup
#define WINDOW_GFX_HEIGHT 400

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
  unsigned char input_buffer[10240];
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
//	field.setup_square( GLASSES_FIRST_ROW , GLASSES_HIGH , false , false , false , true );


	// for temporary 50-glass setup
	field.setup_square( 10 , 5 , false , true , false , true );


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
  unsigned int seq_id=0;
	while( input_data >= 3 )
	{
	  unsigned int r,g,b;
		r = *(input_buffer++);
		g = *(input_buffer++);
		b = *(input_buffer++);
		input_data-=3;
		if(!field.set_sequence_color( seq_id++ , (r)+(g<<8)+(b<<16) ))
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
