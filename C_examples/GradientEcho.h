/* 
  * Copyright (c)  2011, SpinCore Technologies, Inc.
  * All rights reserved.
  *
  * This program is free software: you can redistribute it and/or modify
  * it under the terms of the GNU General Public License as published by
  * the Free Software Foundation, either version 3 of the License, or
  * (at your option) any later version.
  * 
  * This program is distributed in the hope that it will be useful,
  * but WITHOUT ANY WARRANTY; without even the implied warranty of
  * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  * GNU General Public License for more details.
  * 
  * You should have received a copy of the GNU General Public License
  *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
  */

typedef struct SCANPARAMS
{
	// User Inputted Values
	unsigned int nPoints;
	unsigned int nScans;
	unsigned int nPhases;
	double spectrometerFrequency_MHz;
	double spectralWidth_kHz;
	double pulseTime_us;
	double transTime_us;
	double phaseTime_us;
	double repetitionDelay_s;
	double tx_phase;
	double amplitude;
	unsigned int blankingBit;
	double blankingDelay_ms;
	int adcOffset; // 74 for K004
	char* outputFilename;
	
	// Added Parameters
	double echoDelayTime_us;
	double lb_value; // line broadening value: 0 is none, 1 is a small amount, 5 is lots (maybe too much)
	int shapeRF; // number of lobes for a sinc pulse (0 = no shape)
	
	int slice_en;
	int phase_en;
	int readout_en;
	
	
	int verbose;
	
	// Derived Values
	double actualSpectralWidth_Hz;
	double adcFrequency_MHz;
	double acqTime_ms;
	
} SCANPARAMS;

DWORD error_catch(int error, int line_number);
int processArguments(int argc, char* argv[], SCANPARAMS* scanParams);
int verifyArguments(SCANPARAMS * scanParams);
int configureBoard(SCANPARAMS * scanParams);
int programBoard(SCANPARAMS * scanParams);
int runScan(SCANPARAMS * scanParams);
int readData(SCANPARAMS * scanParams);
