#include "hexfield.h"

#define NO_SEQ (~((unsigned int)0))

#define PAIR_GET_X(v)     (int)((short)( (v)&0x0000FFFFu ))
#define PAIR_GET_Y(v)     (int)((short)( (v)>>16 ))
#define PAIR_BUILD(x,y)   ( ((unsigned int)(unsigned short)(x)) + (((unsigned int)(y))<<16) )


HexArray::HexArray()
{
	reset();
}

HexArray::~HexArray()
{
}

void HexArray::reset()
{
	m_grid_2_seq.clear();
	m_seq_2_grid.clear();
	m_rgb.clear();
	m_grid_x0=0;
	m_grid_y0=0;
	m_grid_width=1;
	m_grid_2_seq.push_back(NO_SEQ);
}

void HexArray::setup_square(unsigned int len_row_0,unsigned int rows,bool first_indented_left,bool first_indented_right,bool start_first_reversed,bool zigzag)
{
  int gw,indent;
  bool toright;
  unsigned int seq;
  int y;
  int x0;
	gw=len_row_0*2-1;indent=0;
	if(first_indented_left)
		{gw++;indent=1;}
	if(first_indented_right)
		{gw++;}
	toright = !start_first_reversed;

	seq = 0;y=0;x0=0;

	reset();

	while(rows>0)
	{
		if(toright)
		{
			for( int x=indent ; x<gw ; x+=2 )
				set( seq++ , (x>>1)+x0 , y , 0x000000 );
		}else{
			for( int x=((gw-1-indent)&(~1))+indent ; x>=0 ; x-=2 )
				set( seq++ , (x>>1)+x0 , y , 0x000000 );
		}
		if(indent)
			x0--;
		indent = indent^1;
		if(zigzag)
			toright = !toright;

		rows--;y++;
	}

}

void HexArray::setup_triangle(unsigned int edge_len,bool start_first_reversed,bool zigzag)
{
  bool toright;
  unsigned int seq;
  int y;
	toright = !start_first_reversed;

	seq=0;y=0;

	reset();

	while(edge_len>0)
	{
		if(toright)
		{
			for( int x=0 ; x<(int)edge_len ; x++ )
				set( seq++ , x , y , 0x000000 );
		}else{
			for( int x=edge_len-1 ; x>=0 ; x-- )
				set( seq++ , x , y , 0x000000 );
		}
		if(zigzag)
			toright = !toright;

		edge_len--;y++;
	}
}

bool HexArray::get_sequence_item(unsigned int seq_id,int *out_w,int *out_h,unsigned int *out_color) const
{
  int x,y;
  unsigned int v;
	if( seq_id >= (unsigned int)m_seq_2_grid.size() )
		return false;
	v = m_seq_2_grid[seq_id];
	x = PAIR_GET_X(v);
	y = PAIR_GET_Y(v);
	*out_w = 2*x + y ;
	*out_h = 2*y;
	*out_color = m_rgb[seq_id];
	return true;
}

bool HexArray::set_sequence_color(unsigned int seq_id,unsigned int color)
{
	if( seq_id >= (unsigned int)m_seq_2_grid.size() )
		return false;
	m_rgb[seq_id] = color;
	return true;
}

void HexArray::set(unsigned int seq_idx,int x,int y,unsigned int color)
{
  bool bres;
	// stretch ?
	if( y < m_grid_y0 )
	{
		if( x < m_grid_x0 )
			bres = stretch( (m_grid_x0-x) , 0 , (m_grid_y0-y) );
		else if( x >= m_grid_x0+m_grid_width )
			bres = stretch( 0 , (x+1)-(m_grid_x0+m_grid_width) , (m_grid_y0-y) );
		else
			bres = stretch( 0 , 0 , (m_grid_y0-y) );
	}else{
		if( x < m_grid_x0 )
			bres = stretch( (m_grid_x0-x) , 0 , 0 );
		else if( x >= m_grid_x0+m_grid_width )
			bres = stretch( 0 , (x+1)-(m_grid_x0+m_grid_width) , 0 );
		else
			bres = true;
	}
	if(!bres)
		return;			// assert?

  int arpos;
	arpos = (x-m_grid_x0) + (y-m_grid_y0)*m_grid_width ;
	while( arpos >= (int)m_grid_2_seq.size() )
		m_grid_2_seq.push_back(NO_SEQ);
	m_grid_2_seq[arpos] = seq_idx;

	while( seq_idx >= m_seq_2_grid.size() )
		m_seq_2_grid.push_back(0);
	m_seq_2_grid[seq_idx] = PAIR_BUILD(x,y);

	while( seq_idx >= m_rgb.size() )
		m_rgb.push_back(0);
	m_rgb[seq_idx] = color;
}

bool HexArray::stretch(int add_x_min,int add_x_max,int add_y_min)
{
  unsigned int newW;
	if( add_x_min<0 || add_x_max<0 || add_y_min<0 )
		return false;
	newW = m_grid_width+add_x_min+add_x_max;
	if( add_x_min>=0x010000 || add_x_max>=0x10000 || add_y_min>=0x010000 || newW>=0x010000 )
		return false;
	// just clear and re-fill
	for( std::vector<unsigned int>::iterator it=m_grid_2_seq.begin() ; it!=m_grid_2_seq.end() ; ++it )
		{*it = NO_SEQ;}
	// scan other array and fill.
	for( std::vector<unsigned int>::const_iterator it=m_seq_2_grid.begin() ; it!=m_seq_2_grid.end() ; ++it )
	{
	  unsigned int s2g_val;
	  unsigned int arpos;
	  int x,y;
		s2g_val = *it;
		// calc old coordinate from it.
		x = PAIR_GET_X(s2g_val);
		y = PAIR_GET_Y(s2g_val);
		// rebuild
		arpos = (y+add_y_min-m_grid_y0)*newW + (x+add_x_min-m_grid_x0) ;
		// place to arrays
		while( arpos >= m_grid_2_seq.size() )
			m_grid_2_seq.push_back(NO_SEQ);
		m_grid_2_seq[arpos] = (unsigned int)(it-m_seq_2_grid.begin());
	}

	m_grid_x0 -= add_x_min;
	m_grid_y0 -= add_y_min;
	m_grid_width += (add_x_min+add_x_max);

	return true;
}
