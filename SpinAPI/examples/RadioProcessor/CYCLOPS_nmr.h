/* Copyright (c) 2009 SpinCore Technologies, Inc.
 *   http://www.spincore.com
 *
 * This software is provided 'as-is', without any express or implied warranty. 
 * In no event will the authors be held liable for any damages arising from the 
 * use of this software.
 *
 * Permission is granted to anyone to use this software for any purpose, 
 * including commercial applications, and to alter it and redistribute it
 * freely, subject to the following restrictions:
 *
 * 1. The origin of this software must not be misrepresented; you must not
 * claim that you wrote the original software. If you use this software in a
 * product, an acknowledgment in the product documentation would be appreciated
 * but is not required.
 * 2. Altered source versions must be plainly marked as such, and must not be
 * misrepresented as being the original software.
 * 3. This notice may not be removed or altered from any source distribution.
 */
 
/**
 * CYCLOPS_nmr.h
 * This program is used to control the RadioProcessor series of boards.
 * This file contains constants and data structures used by spinnmr.c. 
 *
 * SpinCore Technologies, Inc.
 * www.spincore.com
 * $Date: 2008/05/21 15:04:05 $
 */

#define NUM_ARGUMENTS 33
#define FNAME_SIZE 256
#define MAX_FFT 32768

#define BOARD_STATUS_IDLE 0x3
#define BOARD_STATUS_BUSY 0x6

// User friendly names for the phase registers of the cos and sin channels
#define PHASE000 0
#define PHASE090 1
#define PHASE180 2
#define PHASE270 3

// User friendly names for the control bits
#define TX_ENABLE 1
#define TX_DISABLE 0
#define PHASE_RESET 1
#define NO_PHASE_RESET 0
#define DO_TRIGGER 1
#define NO_TRIGGER 0
#define AMP0 0

#define ADD 1
#define SUB 0
#define	SWAP 1
#define NO_SWAP 0

// Error return values for spinnmr
#define INVALID_ARGUMENTS      -1
#define BOARD_NOT_DETECTED     -2
#define INVALID_NUM_ARGUMENTS  -3
#define RX_AND_TX_DISABLED     -4
#define INVALID_DATA_FROM_BOARD -5
#define PROGRAMMING_FAILED     -6


typedef struct SCANPARAMS
{
	char* outputFilename;
	
	int board_num;
	
	unsigned int nPoints;
	unsigned int nScans;
	unsigned short bypass_fir;
	unsigned short use_shape;
	unsigned short enable_rx;
	unsigned short enable_tx;
	unsigned short verbose;
	unsigned short debug;
	
	double spectrometerFrequency;
	double spectralWidth;
	double actualSpectralWidth;
	double pulseTime;
	double transTime;
	double repetitionDelay;
	double adcFrequency;
	double amplitude;
    double tx_phase;
    
    double wait_time;
    
    char blankingEnable;
    char blankingBit;
    double blankingDelay;
    
} SCANPARAMS;

typedef struct CYCLOPSPARAMS
{
    int phase_0;
	int add_sub_re_0;
	int add_sub_im_0;
	int swap_0;

    int phase_1;
	int add_sub_re_1;
	int add_sub_im_1;
	int swap_1;

    int phase_2;
	int add_sub_re_2;
	int add_sub_im_2;
	int swap_2;

    int phase_3;
	int add_sub_re_3;
	int add_sub_im_3;
	int swap_3;   
	
} CYCLOPSPARAMS;

//--------------------------------------------------------------------	

void make_shape_data(float* shape_array, void* arg, void (*shapefnc)(float*,void*) ); //This function will generate the shape data for the board using the shapefnc argument.

void shape_sinc(float* shape_array, void* nlobe); //Creates shape data. To be used with make_shape_data

int processArguments(int argc, char* argv[], SCANPARAMS* scanParams, CYCLOPSPARAMS* cyclopsParams); //Process argc and argv and fills in the scanParams and cyclopsParams structures.

int verifyArguments(SCANPARAMS* scanParams, int verbose); //CHecks the boundary conditions of the arguments.

void outputScanParams(SCANPARAMS* myScan); //Prints the SCANPARAMS structure.

int configureBoard(SCANPARAMS*); //Sets the board defaults.

int programBoard(SCANPARAMS* myScan, CYCLOPSPARAMS* cycScan); //Programs the phase and frequency registers as well as the pulse program.

double checkUndersampling(SCANPARAMS*,int); //Checks to see if undersampling is needed. (Spectral Frequency > Nyquist)

void printTitleBlock(SCANPARAMS * myScan, char *title_string); //Prints scan information to Felix .fid file title block.

//--------------------------------------------------------------------
