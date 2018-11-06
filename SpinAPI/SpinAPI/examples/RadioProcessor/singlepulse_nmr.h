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
 * singlepulse_nmr.h
 * Modified from singlepulse_nmr.h
 *
 *	This program is used to control the RadioProcessor series of boards in conjuction with the iSpin setup.
 *	It generates a single RF pulse of variable shape, frequency, amplitude, phase and duration.
 *	It then acquires the NMR response of the perturbing pulse.
 
 * SpinCore Technologies, Inc.
 * www.spincore.com
 * $Date: 2017/07/11 11:00:00 $
 */

#define NUM_ARGUMENTS 19
#define MAX_FFT 48716
#define FNAME_SIZE 256

#define BOARD_STATUS_IDLE 0x3
#define BOARD_STATUS_BUSY 0x6

// User friendly names for the phase registers of the cos and sin channels
#define PHASE000    0
#define PHASE090    1
#define PHASE180    2
#define PHASE270    3

// User friendly names for the control bits
#define TX_ENABLE       1	
#define TX_DISABLE      0
#define PHASE_RESET     1
#define NO_PHASE_RESET  0
#define DO_TRIGGER      1
#define NO_TRIGGER      0
#define AMP0            0
#define BLANK_PA		0x00

// Error return values for Hahn Echo
#define INVALID_ARGUMENTS       -1
#define BOARD_NOT_DETECTED      -2
#define INVALID_NUM_ARGUMENTS   -3
#define RX_AND_TX_DISABLED      -4
#define INVALID_DATA_FROM_BOARD -5
#define PROGRAMMING_FAILED      -6
#define CONFIGURATION_FAILED    -7
#define ALLOCATION_FAILED       -8
#define DATA_RETRIEVAL_FAILED   -9


typedef struct SCANPARAMS
{
	char* file_name;
	
	//Board Parameters
	int board_num;
	char deblank_bit_mask;
	unsigned short deblank_bit;
	unsigned short debug;
	
	//Frequency Parameters
	double ADC_frequency;       //MHz
	double SF;                  //MHz
	double res_frequency;       //MHz
	double SW;                  //kHz
	double actual_SW;           //kHz
    
    //Pulse Parameters
    unsigned short enable_tx;	
    unsigned short use_shape;
    double amplitude;
	double p90_time;            //us
	double p90_phase;           //degrees
    
	//Acquisition Parameters
	unsigned short enable_rx;
	unsigned short bypass_fir;
	unsigned int num_points;
	unsigned int num_scans;
    double scan_time;           //ms
    
	//Delay Parameters
	double deblank_delay;       //ms
	double transient_delay;     //us
	double repetition_delay;    //s	
    
} SCANPARAMS;

//--------------------------------------------------------------------	

int allocInitMem (void **array, int size);

//Parameter Reading
int processArguments(int argc, char* argv[], SCANPARAMS* scanParams); //Process argc and argv and filles in the scanParams structure.

int verifyArguments(SCANPARAMS* scanParams); //CHecks the boundary conditions of the arguments.


//Terminal Output
void printProgramTitle(); //Print the title and SpinAPI version to terminal

inline void printProperUse(); //Prints out the usage data for the executable

void printScanParams(SCANPARAMS* myScan); //Prints the SCANPARAMS structure.


//Board Interfacing
int configureBoard(SCANPARAMS*); //Sets the board defaults.

int programBoard(SCANPARAMS*); //Programs the phase and frequency registers as well as the pulse program.


//File Writing
void createFelixTitleBlock(SCANPARAMS* myScan, char* title_string); //Prints scan info to Felix (.fid) title block

void writeDataToFiles(SCANPARAMS* myScan, int* real, int* imag); //Output acquisition results to ASCII, Felix, and Jcamp


//Calculations
void make_shape_data(float* shape_array, void* arg, void (*shapefnc)(float*,void*) ); //This function will generate the shape data for the board using the shapefnc argument.

void shape_sinc(float* shape_array, void* nlobe); //Creates shape data. To be used with make_shape_data

double checkUndersampling(SCANPARAMS*); //Checks to see if undersampling is needed. (Spectral Frequency > Nyquist)

int roundUpPower2(int number); //Round up to the nearest power of 2
//--------------------------------------------------------------------
