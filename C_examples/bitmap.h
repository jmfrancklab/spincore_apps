// Header file for simple bitmap library
#include <stdlib.h>
#include <stdio.h>
#include <stddef.h>
#include <stdint.h>

#ifndef BITMAP_H
#define BITMAP_H

typedef struct tagPIXELCOLOR {
	char r;
	char g;
	char b;
} PIXELCOLOR;

typedef struct tagBITMAPFILEHEADER {
	uint32_t bfSize;
	uint16_t bfReserved1;
	uint16_t bfReserved2;
	uint32_t bfOffBits;
} BITMAPFILEHEADER, BMPFH;

typedef struct tagBITMAPINFOHEADER { 
 	uint32_t biSize;
 	int32_t biWidth;
 	int32_t biHeight;
 	int16_t biPlanes;
 	int16_t biBitCount;
 	uint32_t biCompression;
 	uint32_t biSizeImage;
 	int32_t biXPelsPerMeter;
 	int32_t biYPelsPerMeter;
 	uint32_t biClrUsed;
 	uint32_t biClrImportant;
} BITMAPINFOHEADER, BMPIH;

typedef struct tagIMAGE {
	int columns;
	int rows;
	PIXELCOLOR** pixel;
} IMAGE;

typedef struct tagBMPFILE {
	FILE* bmp_file;
	int fopen;
	BMPFH bmpfh;
	BMPIH bmpih;
	int row_padding;
	int current_row;
	int current_column;
	int num_rows;
	int num_cols;
} BMPFILE;

/**
  * Colormap structure
  * Contains key colors for color interpolation done by bmp_color_conv(...) and
  * bmp_swrite_map(...)
  */
typedef struct tagCOLORMAP{
	int key_colors;
	unsigned char* r;
	unsigned char* g;
	unsigned char* b;
	double* color;
} COLORMAP;

// internal functions
int bmp_create_file_header( IMAGE* image, BMPFH* bmp_file_header );
int bmp_create_info_header( IMAGE* image, BMPIH* bmp_info_header );
int bmp_create_data( IMAGE* image, char* data );
int bmp_color_conv( double color, unsigned char* r, unsigned char* g, unsigned char* b, COLORMAP map);


// block write
int bmp_write_image_to_bmp( IMAGE* image, char* file_name );

// streaming write
int bmp_init_swrite( BMPFILE* bmp, int rows, int cols, char* file_name );
int bmp_swrite( BMPFILE* bmp, unsigned char r, unsigned char g, unsigned char b );
int bmp_swrite_map( BMPFILE* bmp, double color, COLORMAP map );
double bmp_swrite_progress( BMPFILE* bmp );

#endif
