/* T1_IR_sweep.h   
 *
 * Modified from Stimulated_echo.h by 
 * 
 *     Tycho Sleator 
 *     New York University
 *     Department of Physics
 *     4 Washington Place
 *     New York, NY 10027
 *     email:  tycho.sleator@nyu.edu. 
 *
 * Last Edit 11/26/2013: 11:23:00
 */


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
 *
 * SpinCore Technologies, Inc.
 * www.spincore.com
 * $Date: 2008/05/21 15:04:05 $
 */


#define NUM_ARGUMENTS 21
#define FNAME_SIZE 256

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

// Error return values for CPMG
#define INVALID_ARGUMENTS      -1
#define BOARD_NOT_DETECTED     -2
#define INVALID_NUM_ARGUMENTS  -3
#define RX_AND_TX_DISABLED     -4
#define INVALID_DATA_FROM_BOARD -5
#define PROGRAMMING_FAILED     -6


typedef struct SCANPARAMS
{
	char* fname;
	
	int board_num;
	
	unsigned int num_scans;
	unsigned short bypass_fir;
	unsigned int blankBit;
	unsigned short debug;
	unsigned int n_tau;
	unsigned int i_tau;  
	
	double SF;
	double SW;
	double actualSpectralWidth;
	double p1_time;
	double p2_time;
	double ringdown_time;
	double p1_phase;
	double p2_phase;
	double fid_time;
	double tau_min;
	double delta_tau;
	double tau;
	double repetition_delay;
	double amplitude;
	double blankDelay;
	double adcFrequency;

	char blankMask;
} SCANPARAMS;

//--------------------------------------------------------------------	

int processArguments(int argc, char* argv[], SCANPARAMS* scanParams); //Process argc and argv and fills in the scanParams structure.

int verifyArguments(SCANPARAMS* scanParams); //Checks the boundary conditions of the arguments.

int runPulseProgram(SCANPARAMS * myScan); // Programs and runs the pulse program and saves the data to a file.  

void outputScanParams(SCANPARAMS* myScan); //Prints the SCANPARAMS structure.

// double checkUndersampling(SCANPARAMS*,int); //Checks to see if undersampling is needed. (Spectral Frequency > Nyquist)

static inline void printProperUse(); //Prints out the usage data for the executable

void printTitleBlock(SCANPARAMS* myScan, char* title_string); //Prints scan info to Felix (.fid) title block

//--------------------------------------------------------------------
