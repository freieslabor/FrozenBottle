#ifndef HEXFIELD_H
#define HEXFIELD_H

#include <math.h>
#include <vector>

// representation is right-skewed rectangular.
// diagram of a 4*4 cells array, viewed as hexes and as 2D array:
//
//     C D E F      CDEF
//    8 9 A B       89AB
//   4 5 6 7        4567
//  0 1 2 3         0123
//
// a triangle of hexes, viewed as the 2D array (dots are unused but allocated spaces):
//
//     9            9...
//    7 8           78..
//   4 5 6          456.
//  0 1 2 3         0123
//
// sample 'square' hexes box.
//
//   N O P Q         NOPQ...
//  I J K L M        IJKLM..
//   E F G H         .EFGH..
//  9 A B C D        .9ABCD.
//   5 6 7 8         ..5678.
//  0 1 2 3 4        ..01234
//
// holds two arrays: mapping of square-grid (right diagrams) to LED-sequence
//                   mapping of sequence to square-grid offset (x+w*y)


class HexArray
{
  public:
	HexArray();		// creates empty. use setup() function
	~HexArray();

	void reset();	// wipes array to empty.

	/// setup function for a rectangle build
	void setup_square(unsigned int len_row_0,unsigned int rows,bool first_indented_left,bool first_indented_right,bool start_first_reversed,bool zigzag);
	/// setup function for a triangle build
	void setup_triangle(unsigned int edge_len,bool start_first_reversed,bool zigzag);


	// get an item. returned coordinates are screen-rect-coords. W-step is 2, next row is interleaved in it.
	bool get_sequence_item(unsigned int seq_id,float *out_w,float *out_h,unsigned int *out_color) const;

	// query number of sequence items
	unsigned int get_sequence_count() const;

	// set one color value
	bool set_sequence_color(unsigned int seq_id,unsigned int color);


  private:
	void set(unsigned int seq_idx,int x,int y);
	bool stretch(int add_x_min,int add_x_max,int add_y_min);

	std::vector<unsigned int> m_grid_2_seq;	// 2D array, contains sequence-numbers or NO_SEQ
	int m_grid_x0;
	int m_grid_y0;
	int m_grid_width;
	std::vector<unsigned int> m_seq_2_grid;	// 1D array, contains X/Y pairs (Y in high-bits)
	std::vector<unsigned int> m_rgb;	// 1D array, contains volor values
};








#endif
