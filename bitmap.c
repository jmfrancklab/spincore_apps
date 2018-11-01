/**
  * Simple bitmap writing library
  * This library can be used in one of two ways:
  *   Block Write:
  *     1) Make an IMAGE structure and use the function:
  *       int bmp_write_image_to_bmp( IMAGE* image, char* file_name );
  *   Streaming Write:
  *     1) Initialize the bitmap file and BMP structure by using:
  *       int bmp_init_swrite( BMPFILE* bmp, int rows, int cols,
  *                            char* file_name );
  *     2) Write point by point by using the function:
  *       int bmp_swrite( BMPFILE* bmp, unsigned char r,
  *                       unsigned char g, unsigned char b );
  *     or the function:
  *       int bmp_swrite_map( BMPFILE* bmp, double color, COLORMAP map );
  */

#include "bitmap.h"

/**
 * This function fills up the file header for a bitmap file
 */
int bmp_create_file_header( IMAGE* image, BMPFH* bmp_file_header )
{	
	int row_size = image->columns * 3;
	// This makes sure that the rows are padded to end on a DWORD boundry
	if( row_size % 4 != 0 ) {
		row_size = row_size + ( 4 - (row_size % 4) );
	}
	
	bmp_file_header->bfSize = 54 + row_size * image->rows; // size of bmp file in bytes
	bmp_file_header->bfReserved1 = 0;
	bmp_file_header->bfReserved2 = 0;
	bmp_file_header->bfOffBits = 54; // address offset for data
	return 0;
}


/**
  * This function fills up the info header for a bitmap file
  */
int bmp_create_info_header( IMAGE* image, BMPIH* bmp_info_header )
{
	bmp_info_header->biSize = 40;
	bmp_info_header->biWidth = image->columns;
	bmp_info_header->biHeight = image->rows;
	bmp_info_header->biPlanes = 1;
	bmp_info_header->biBitCount = 24;
	bmp_info_header->biCompression = 0;
	
	int row_size = image->columns * 3;
	// This makes sure that the rows are padded to end on a DWORD boundry
	if( row_size % 4 != 0 ) {
		row_size = row_size + ( 4 - (row_size % 4) );
	}
	
	bmp_info_header->biSizeImage = row_size * image->rows;
	bmp_info_header->biXPelsPerMeter = 0;
	bmp_info_header->biYPelsPerMeter = 0;
	bmp_info_header->biClrUsed = 0;
	bmp_info_header->biClrImportant = 0;
	return 0;
}


/** 
  * This function fills up the data portion of a bitmap file
  * 
  * data needs to be the large enough
  * (columns + 1) * rows * 3 is a safe size
  */
int bmp_create_data( IMAGE* image, char* data )
{
	int padding;
	if( ( image->columns * 3 ) % 4 == 0 ) {
		padding = 0;
	} else {
		padding = 4 - ( ( image->columns * 3 ) % 4 );
	}
	int index = 0;
	int p;
	int row;
	int col;
	// bottom up, left to right
	for( row = (image->rows - 1) ; row >= 0 ; row-- ) {
		for( col = 0 ; col < image->columns ; col++ ) {
			data[index] = image->pixel[row][col].b;
			index++;
			data[index] = image->pixel[row][col].g;
			index++;
			data[index] = image->pixel[row][col].r;
			index++;
		}
		for( p = 0 ; p < padding ; p++ ) {
			data[index] = 0;
			index++;
		}
	}
	return 0;
}

/**
  * Converts magnitude value to RGB value according to a provided colormap.
  * The RGB color comes from linear interpolation between the key colors of the
  * colormap.
  */
int bmp_color_conv( double color, unsigned char* r, unsigned char* g, unsigned char* b, COLORMAP map) {
	int i;
	double ratio;
	
	//default to color > map.color[map.points-1]
	*r = map.r[map.key_colors-1];
	*g = map.g[map.key_colors-1];
	*b = map.b[map.key_colors-1];
	
	if( color <= map.color[0] ) {
		*r = map.r[0];
		*g = map.g[0];
		*b = map.b[0];
	}
	
	for( i = 0 ; i < (map.key_colors - 1) ; i++ ) {
		if( color > map.color[i] && color <= map.color[i+1] ) {
			if( map.color[i] == map.color[i+1] ) {
				ratio = 0;
			} else {
				ratio = (color - map.color[i])/(map.color[i+1] - map.color[i]);
			}
			*r = map.r[i] + (map.r[i+1] - map.r[i]) * ratio;
			*g = map.g[i] + (map.g[i+1] - map.g[i]) * ratio;
			*b = map.b[i] + (map.b[i+1] - map.b[i]) * ratio;
		}
	}
	
	return 0;
}


/**
  * This function writes an IMAGE to a bitmap file
  */
int bmp_write_image_to_bmp( IMAGE* image, char* file_name ) {
	BMPFH* bmp_file_header = malloc(sizeof(BMPFH));
	BMPIH* bmp_info_header = malloc(sizeof(BMPIH));
	char* bmp_data;
	FILE* fp;
	if( bmp_file_header == NULL || bmp_info_header == NULL ) {
		return -1;
	}
	bmp_create_file_header( image, bmp_file_header );
	bmp_create_info_header( image, bmp_info_header );
	bmp_data = malloc( bmp_info_header->biSizeImage );
	if( bmp_data == NULL ) {
		return -1;
	}
	
	bmp_create_data( image, bmp_data );
	// Write file
	fp = fopen( file_name, "wb" );
	if( fp == NULL ) {
		return -1;
	}
	uint16_t magic_number = 19778;
	fwrite( &magic_number, sizeof(uint16_t), 1, fp );
	fwrite( bmp_file_header, sizeof(BMPFH), 1, fp );
	fwrite( bmp_info_header, sizeof(BMPIH), 1, fp );
	fwrite( bmp_data, sizeof(char), bmp_info_header->biSizeImage, fp );
	fclose( fp );
	free( bmp_file_header );
	free( bmp_info_header );
	free( bmp_data );
	return 0;
}

/**
  * This functions initializes writing a bitmap using the streaming method
  */
int bmp_init_swrite( BMPFILE* bmp, int rows, int cols, char* file_name )
{
	// Input error checking
	if( bmp == NULL ) {
		return -1;
	}
	if( rows == 0 || cols <= 0 ) {
		return -1;
	}
	
	IMAGE* im = malloc( sizeof(IMAGE) );
	BMPFH bmp_file_header;
	BMPIH bmp_info_header;
	
	// Prepare the headers for the bmp file
	im->rows = rows;
	im->columns = cols;
	bmp_create_file_header( im, &bmp_file_header );
	bmp_create_info_header( im, &bmp_info_header );
	free( im );
	
	// Initialize BMPFILE structure
	bmp->bmp_file = fopen( file_name, "wb" );
	if( bmp->bmp_file == NULL ) {
		return -1;
	}
	bmp->fopen = 1;
	bmp->bmpfh = bmp_file_header;
	bmp->bmpih = bmp_info_header;
	bmp->num_rows = rows;
	bmp->num_cols = cols;
	if( rows < 0 ) {
		// scanning rows top to bottom
		bmp->current_row = 0;
	} else {
		// scanning rows bottom to top
		bmp->current_row = rows - 1;
	}
	bmp->current_column = 0;
	if( (cols * 3) % 4 == 0 ) {
		bmp->row_padding = 0;
	} else {
		bmp->row_padding = 4 - ((cols * 3) % 4);
	}
	
	// Writing the header for the bmp file
	uint16_t magic_number = 19778;
	fwrite( &magic_number, sizeof(uint16_t), 1, bmp->bmp_file );
	fwrite( &bmp_file_header, sizeof(BMPFH), 1, bmp->bmp_file );
	fwrite( &bmp_info_header, sizeof(BMPIH), 1, bmp->bmp_file );
	
	return 0;
}

/**
  * This function writes the bitmap pixel by pixel.
  * Use bmp->current_row and bmp->current_column to find out what pixel will be
  * written next.
  */
int bmp_swrite( BMPFILE* bmp, unsigned char r, unsigned char g, unsigned char b )
{
	// check to see if the bmp file is finished yet
	if( bmp->fopen != 1 ) {
		return -1;
	}
	
	// write the colors to the file
	fputc( (int) b, bmp->bmp_file );
	fputc( (int) g, bmp->bmp_file );
	fputc( (int) r, bmp->bmp_file );
	
	bmp->current_column++;
	
	int p;
	
	// check to see if the row is now finished
	if( bmp->current_column >= bmp->bmpih.biWidth ) {
		// pad the row so it ends on a dword boundary
		for( p = 0 ; p < bmp->row_padding ; p++ ) {
			fputc( 0, bmp->bmp_file );
		}
		
		bmp->current_column = 0;
		
		// check to see if the rows should be decreasing or increasing
		if( bmp->bmpih.biHeight < 0 ) {
			bmp->current_row++;
			
			// check to see if the image is done
			if( bmp->current_row == bmp->bmpih.biHeight ) {
				fclose( bmp->bmp_file );
				bmp->fopen = 0;
			}
		} else {
			bmp->current_row--;
			
			// check to see if the image is done
			if( bmp->current_row == -1 ) {
				fclose( bmp->bmp_file );
				bmp->fopen = 0;
			}
		}
	}
	
	return 0;
}

/**
  * This function writes the bitmap pixel by pixel using magnitude color data.
  * The color data is changed into RGB data according to the color map.
  * Use bmp->current_row and bmp->current_column to find out what pixel will be
  * written next.
  */
int bmp_swrite_map( BMPFILE* bmp, double color, COLORMAP map )
{
	unsigned char r, g, b;
	bmp_color_conv( color, &r, &g, &b, map);
	return bmp_swrite( bmp, r, g, b );
}

/**
  * This function outputs the proportion of the image that has been written
  * already as a double ranging from 0.0 to 1.0.
  */
double bmp_swrite_progress( BMPFILE* bmp )
{
	int full_rows;
	int total_points;
	if( bmp->num_rows < 0 ) {
		total_points = -(bmp->num_rows) * bmp->num_cols;
		full_rows = bmp->current_row;
	} else {
		total_points = bmp->num_rows * bmp->num_cols;
		full_rows = bmp->num_rows - bmp->current_row - 1;
	}
	return ((double) full_rows * bmp->num_cols + bmp->current_column) / (double) total_points;
}

