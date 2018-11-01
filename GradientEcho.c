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

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#include "mrispinapi.h"
#include "bitmap.h"
#include "fftw3.h"
#include "GradientEcho.h"

#define NUM_ARGUMENTS 21

#define SLICE_RISETIME_US 100

#define END_PHASE 1.0
#define START_PHASE -1.0

#define ERROR_CATCH(arg) error_catch(arg, __LINE__)

void pause(void)
{
	printf("Press enter to exit...");
	// flushing input stream doesn't work on all platforms
	fflush(stdin);
	fgetc(stdin);
}

DWORD error_catch(int error, int line_number)
{
	if( error != 0 ) {
		printf("ERROR CODE 0x%X AT LINE NUMBER %d\n", error, line_number);
		pause();
		exit(1);
	}
	return error;
}


int main(int argc, char *argv[])
{
	SCANPARAMS myScan;
	
	ERROR_CATCH( processArguments(argc, argv, &myScan) );
	ERROR_CATCH( verifyArguments( &myScan ) );
	ERROR_CATCH( configureBoard( &myScan ) );
	ERROR_CATCH( programBoard( &myScan ) );
	ERROR_CATCH( runScan( &myScan ) );
	ERROR_CATCH( readData( &myScan) );
	
	return 0;
}


int processArguments(int argc, char* argv[], SCANPARAMS* scanParams)
{
	if (argc - 1 < NUM_ARGUMENTS)
	{
		printf("Error: Improper number of arguments\n");
		return -1;
	}
	
	scanParams->nPoints = atoi (argv[1]);
	scanParams->nScans = atoi (argv[2]);
	scanParams->nPhases = atoi (argv[3]);
	scanParams->spectrometerFrequency_MHz = atof (argv[4]);
	scanParams->spectralWidth_kHz = atof (argv[5]);
	scanParams->pulseTime_us = atof (argv[6]);
	scanParams->transTime_us = atof (argv[7]);
	scanParams->phaseTime_us = atof (argv[8]);
	scanParams->repetitionDelay_s = atof (argv[9]);
	scanParams->tx_phase = atof (argv[10]);
	scanParams->amplitude = atof (argv[11]);
	scanParams->blankingBit = atoi (argv[12]);
	scanParams->blankingDelay_ms = atof (argv[13]);
	scanParams->adcOffset = atoi (argv[14]);
	scanParams->outputFilename = argv[15];
	
	// Added parameters
	scanParams->echoDelayTime_us = atof(argv[16]);
	scanParams->lb_value = atof(argv[17]);
	scanParams->shapeRF = atoi(argv[18]);
	
	// Gradient enables
	scanParams->slice_en = atoi(argv[19]);
	scanParams->phase_en = atoi(argv[20]);
	scanParams->readout_en = atoi(argv[21]);
	
	if( argc - 1 > NUM_ARGUMENTS ) {
		scanParams->verbose = atoi (argv[22]);
	} else {
		scanParams->verbose = 1;
	}
	
	scanParams->adcFrequency_MHz = 75.0;
	
	return 0;
}


int verifyArguments(SCANPARAMS * scanParams)
{
	if (scanParams->nPoints > 16*1024 || scanParams->nPoints < 1)
	{
		printf ("Error: Maximum number of points is 16384.\n");
		return -1;
	}
	
	if (scanParams->nScans < 1)
	{
		printf ("Error: There must be at least one scan.\n");
		return -1;
	}

	if (scanParams->pulseTime_us < 0.065)
	{
		printf ("Error: Pulse time is too small to work with board.\n");
		return -1;
	}

	if (scanParams->transTime_us < 0.065)
	{
		printf ("Error: Transient time is too small to work with board.\n");
		return -1;
	}

	if (scanParams->repetitionDelay_s <= 0)
	{
		printf ("Error: Repetition delay is too small.\n");
		return -1;
	}

	if (scanParams->amplitude < 0.0 || scanParams->amplitude > 1.0)
	{
		printf ("Error: Amplitude value out of range.\n");
		return -1;
	}
	
	if (scanParams->blankingBit < 0 || scanParams->blankingBit > 3)
	{
		printf("Error: Invalid blanking bit specified.\n");
		return -1;
	}
	
	return 0;
}


int configureBoard(SCANPARAMS * scanParams)
{
	double actual_SW;
	double spectralWidth_MHz = scanParams->spectralWidth_kHz / 1000.0;
	int dec_amount;
	int i;
	
	ERROR_CATCH( spmri_init() );
	
	ERROR_CATCH( spmri_set_defaults() );
	
	// ADC offset
	ERROR_CATCH( spmri_set_adc_offset( scanParams->adcOffset ) );
	
	// Carrier Shape
	double carrier[1024];
	for( i = 0 ; i < 1024 ; i++ ) {
		carrier[i] = sin( (double) i / 1024.0 * 2 * 3.14159 );
	}
	ERROR_CATCH(spmri_set_carrier_shape( carrier, 1024 ));
	
	// Carrier Frequency Registers
	double freqs[1] = {scanParams->spectrometerFrequency_MHz}; // MHz
	ERROR_CATCH(spmri_set_frequency_registers( freqs, 1 ));
	
	// Envelope Shape
	double envelope[1024];
	for( i = 0 ; i < 1024 ; i++ ) {
		if( scanParams->shapeRF == 0 ) {
			envelope[i] = 1.0;
		} else {
			if(i == 512) {
				envelope[i] = 1.0;
			} else {
				envelope[i] = sin((i-512)/512.0 * scanParams->shapeRF * 3.14159) / ((i-512)/512.0 * scanParams->shapeRF * 3.14159);
			}
		}
	}
	ERROR_CATCH(spmri_set_envelope_shape( envelope, 1024 ));
	
	// Envelope Frequency Registers
	double env_freqs[1] = {1 / scanParams->pulseTime_us}; // MHz
	ERROR_CATCH(spmri_set_envelope_frequency_registers( env_freqs, 1 ));
	
	// Phase Registers
	double phases[1] = {scanParams->tx_phase};
	ERROR_CATCH(spmri_set_phase_registers( phases, 1 ));
	
	// Amplitude Registers
	double amps[1] = {scanParams->amplitude};
	ERROR_CATCH(spmri_set_amplitude_registers( amps, 1 ));
	
	ERROR_CATCH(spmri_set_num_samples(scanParams->nPoints));
	ERROR_CATCH(spmri_setup_filters(
		spectralWidth_MHz, // Spectral Width in MHz
		scanParams->nScans, // Number of Scans
		0, // Not Used
		&dec_amount
	));
	ERROR_CATCH(spmri_set_num_segments(scanParams->nPhases));
	
	actual_SW = (scanParams->adcFrequency_MHz * 1e6) / (double) dec_amount;
	scanParams->actualSpectralWidth_Hz = actual_SW;
	if( scanParams->verbose ) {
		printf("Decimation              : %d\n", dec_amount);
		printf("Actual Spectral Width   : %f Hz\n",
			scanParams->actualSpectralWidth_Hz);
	}
	
	scanParams->acqTime_ms = scanParams->nPoints / actual_SW * 1000.0;
	
	return 0;
}


int programBoard(SCANPARAMS * scanParams)
{
	DWORD loop_addr;
	int i;
	
	
	// Readout gradient amplitude calculation
	double phasing_readout; // amplitude during phase gradient
	double dephasing_readout; // amplitude during acquisition
	
	if( scanParams->readout_en == 0 ) {
		dephasing_readout = 0.0;
		phasing_readout = 0.0;
	} else if( scanParams->phaseTime_us == 0 ) {
		dephasing_readout = 0.0;
		phasing_readout = -1.0;
	} else if( scanParams->acqTime_ms * ms > 2 * (scanParams->phaseTime_us + 1) * us ) {
		dephasing_readout = 1.0;
		phasing_readout = -2 * (scanParams->phaseTime_us + 1) * us / (scanParams->acqTime_ms * ms);
	} else {
		phasing_readout = -1.0;
		dephasing_readout = scanParams->acqTime_ms * ms / (2 * (scanParams->phaseTime_us + 1) * us);
	}
	
	if( scanParams->verbose ) {
		printf("Dephasing readout amplitude: %f\n", dephasing_readout);
		printf("Phasing readout amplitude: %f\n", phasing_readout);
	}
	
	
	// Slice gradient amplitude calculation
	double slice_amplitude_1; // amplitude during RF pulse
	double slice_amplitude_2; // amplitude during phase gradient
	
	if( scanParams->slice_en == 0 ) {
		slice_amplitude_1 = 0.0;
		slice_amplitude_2 = 0.0;
	} else if( scanParams->phaseTime_us == 0 ) {
		slice_amplitude_1 = 1.0;
		slice_amplitude_2 = 0.0;
	} else if( 2 * scanParams->phaseTime_us > scanParams->phaseTime_us + 2 ) {
		slice_amplitude_1 = 1.0;
		slice_amplitude_2 = -scanParams->pulseTime_us / (2 * (scanParams->phaseTime_us + 2));
	} else {
		slice_amplitude_2 = 1.0;
		slice_amplitude_1 = -(2 * (scanParams->phaseTime_us + 2) / scanParams->pulseTime_us);
	}
	
	if( scanParams->verbose ) {
		printf("Slice amplitude 1: %f\n", slice_amplitude_1);
		printf("Slice amplitude 2: %f\n", slice_amplitude_2);
	}
	
	double phase_amplitude;
	
	
	ERROR_CATCH(spmri_start_programming());
	ERROR_CATCH( spmri_read_addr( &loop_addr ) );
	
	// LOOP instruction
	ERROR_CATCH(spmri_mri_inst(
	  // DAC Information
		0.0, // Amplitude
		ALL_DACS, // DAC Select
		DO_WRITE, // Write
		DO_UPDATE, // Update
		DONT_CLEAR, // Clear
	  // RF Information
		0, // freq register
		0, // phase register
		0, // tx enable
		1, // phase reset
		0, // rx enable
		7, // envelope frequency register (7 = no shape)
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		scanParams->nScans, // data
		LOOP, // opcode
		1.0 * us // delay
	));
	
	for( i = 0 ; i < scanParams->nPhases ; i++ ) {

		// Blanking Delay
		ERROR_CATCH(spmri_mri_inst(
		  // DAC Information
			0.0, // Amplitude
			ALL_DACS, // DAC Select
			DO_WRITE, // Write
			DO_UPDATE, // Update
			DONT_CLEAR, // Clear
		  // RF Information
			0, // freq register
			0, // phase register
			0, // tx enable
			1, // phase reset
			0, // rx enable
			7, // envelope frequency register (7 = no shape)
			0, // amp register
			0, // cyclops phase
		  // Pulse Blaster Information
			0x01 << scanParams->blankingBit, // flags
			0, // data
			CONTINUE, // opcode
			scanParams->blankingDelay_ms * ms // delay
		));
		
		// Slice Gradient
		ERROR_CATCH(spmri_mri_inst(
		  // DAC Information
			slice_amplitude_1, // Amplitude
			SLICE_DAC, // DAC Select
			DO_WRITE, // Write
			DO_UPDATE, // Update
			DONT_CLEAR, // Clear
		  // RF Information
			0, // freq register
			0, // phase register
			0, // tx enable
			1, // phase reset
			0, // rx enable
			7, // envelope frequency register (7 = no shape)
			0, // amp register
			0, // cyclops phase
		  // Pulse Blaster Information
			0x01 << scanParams->blankingBit, // flags
			0, // data
			CONTINUE, // opcode
			SLICE_RISETIME_US * us // delay
		));
			
		if( scanParams->shapeRF ) {
			
			// Shaped RF Pulse
			ERROR_CATCH(spmri_mri_inst(
			  // DAC Information
				0.0, // Amplitude
				ALL_DACS, // DAC Select
				DONT_WRITE, // Write
				DONT_UPDATE, // Update
				DONT_CLEAR, // Clear
			  // RF Information
				0, // freq register
				0, // phase register
				1, // tx enable
				0, // phase reset
				0, // rx enable
				0, // envelope frequency register (7 = no shape)
				0, // amp register
				0, // cyclops phase
			  // Pulse Blaster Information
				0x01 << scanParams->blankingBit, // flags
				0, // data
				CONTINUE, // opcode
				scanParams->pulseTime_us * us // delay
			));
			
		} else {
			
			// Hard RF Pulse
			ERROR_CATCH(spmri_mri_inst(
			  // DAC Information
				0.0, // Amplitude
				ALL_DACS, // DAC Select
				DONT_WRITE, // Write
				DONT_UPDATE, // Update
				DONT_CLEAR, // Clear
			  // RF Information
				0, // freq register
				0, // phase register
				1, // tx enable
				0, // phase reset
				0, // rx enable
				7, // envelope frequency register (7 = no shape)
				0, // amp register
				0, // cyclops phase
			  // Pulse Blaster Information
				0x01 << scanParams->blankingBit, // flags
				0, // data
				CONTINUE, // opcode
				scanParams->pulseTime_us * us // delay
			));
			
		}
		
		// Transient Delay
		ERROR_CATCH(spmri_mri_inst(
		  // DAC Information
			0.0, // Amplitude
			ALL_DACS, // DAC Select
			DO_WRITE, // Write
			DO_UPDATE, // Update
			DONT_CLEAR, // Clear
		  // RF Information
			0, // freq register
			0, // phase register
			0, // tx enable
			0, // phase reset
			0, // rx enable
			7, // envelope frequency register (7 = no shape)
			0, // amp register
			0, // cyclops phase
		  // Pulse Blaster Information
			0x00, // flags
			0, // data
			CONTINUE, // opcode
			scanParams->transTime_us * us // delay
		));
		
		if( scanParams->phaseTime_us > 0 ) {
			// Second Slice Gradient
			ERROR_CATCH(spmri_mri_inst(
			  // DAC Information
				slice_amplitude_1, // Amplitude
				SLICE_DAC, // DAC Select
				DO_WRITE, // Write
				DO_UPDATE, // Update
				DONT_CLEAR, // Clear
			  // RF Information
				0, // freq register
				0, // phase register
				0, // tx enable
				0, // phase reset
				0, // rx enable
				7, // envelope frequency register (7 = no shape)
				0, // amp register
				0, // cyclops phase
			  // Pulse Blaster Information
				0x00, // flags
				0, // data
				CONTINUE, // opcode
				1.0 * us // delay
			));
			
			// Dephasing Readout Gradient
			ERROR_CATCH(spmri_mri_inst(
			  // DAC Information
				dephasing_readout, // Amplitude
				READOUT_DAC, // DAC Select
				DO_WRITE, // Write
				DO_UPDATE, // Update
				DONT_CLEAR, // Clear
			  // RF Information
				0, // freq register
				0, // phase register
				0, // tx enable
				0, // phase reset
				0, // rx enable
				7, // envelope frequency register (7 = no shape)
				0, // amp register
				0, // cyclops phase
			  // Pulse Blaster Information
				0x00, // flags
				0, // data
				CONTINUE, // opcode
				1.0 * us // delay
			));
			
			// phase gradient amplitude calculation
			if( scanParams->phase_en == 0 ) {
				phase_amplitude = 0;
			} else {
				phase_amplitude = (END_PHASE - START_PHASE) * i/(scanParams->nPhases-1) + START_PHASE;
			}
			
			// Phase Gradient
			ERROR_CATCH(spmri_mri_inst(
			  // DAC Information
				phase_amplitude, // Amplitude
				PHASE_DAC, // DAC Select
				DO_WRITE, // Write
				DO_UPDATE, // Update
				DONT_CLEAR, // Clear
			  // RF Information
				0, // freq register
				0, // phase register
				0, // tx enable
				0, // phase reset
				0, // rx enable
				7, // envelope frequency register (7 = no shape)
				0, // amp register
				0, // cyclops phase
			  // Pulse Blaster Information
				0x00, // flags
				0, // data
				CONTINUE, // opcode
				scanParams->phaseTime_us * us // delay
			));
		}
		
		if( scanParams->echoDelayTime_us > 0 ) {
			// Rephasing Readout Gradient and Echo Delay
			ERROR_CATCH(spmri_mri_inst(
			  // DAC Information
				phasing_readout, // Amplitude
				READOUT_DAC, // DAC Select
				DO_WRITE, // Write
				DO_UPDATE, // Update
				DO_CLEAR, // Clear
			  // RF Information
				0, // freq register
				0, // phase register
				0, // tx enable
				0, // phase reset
				0, // rx enable
				7, // envelope frequency register (7 = no shape)
				0, // amp register
				0, // cyclops phase
			  // Pulse Blaster Information
				0x00, // flags
				8, // data
				CONTINUE, // opcode
				scanParams->echoDelayTime_us * us // delay
			));
			
			// Rephasing Readout Gradient and Data Acquisition
			ERROR_CATCH(spmri_mri_inst(
			  // DAC Information
				phasing_readout, // Amplitude
				READOUT_DAC, // DAC Select
				DO_WRITE, // Write
				DO_UPDATE, // Update
				DONT_CLEAR, // Clear
			  // RF Information
				0, // freq register
				0, // phase register
				0, // tx enable
				0, // phase reset
				1, // rx enable
				7, // envelope frequency register (7 = no shape)
				0, // amp register
				0, // cyclops phase
			  // Pulse Blaster Information
				0x00, // flags
				0, // data
				CONTINUE, // opcode
				scanParams->acqTime_ms * ms // delay
			));
		} else {
			// Rephasing Readout Gradient and Data Acquisition
			ERROR_CATCH(spmri_mri_inst(
			  // DAC Information
				phasing_readout, // Amplitude
				READOUT_DAC, // DAC Select
				DO_WRITE, // Write
				DO_UPDATE, // Update
				DO_CLEAR, // Clear
			  // RF Information
				0, // freq register
				0, // phase register
				0, // tx enable
				0, // phase reset
				1, // rx enable
				7, // envelope frequency register (7 = no shape)
				0, // amp register
				0, // cyclops phase
			  // Pulse Blaster Information
				0x00, // flags
				0, // data
				CONTINUE, // opcode
				scanParams->acqTime_ms * ms // delay
			));
		}
		
		// Repetition Delay
		ERROR_CATCH(spmri_mri_inst(
		  // DAC Information
			0.0, // Amplitude
			ALL_DACS, // DAC Select
			DO_WRITE, // Write
			DO_UPDATE, // Update
			DONT_CLEAR, // Clear
		  // RF Information
			0, // freq register
			0, // phase register
			0, // tx enable
			0, // phase reset
			0, // rx enable
			7, // envelope frequency register (7 = no shape)
			0, // amp register
			0, // cyclops phase
		  // Pulse Blaster Information
			0x00, // flags
			0, // data
			CONTINUE, // opcode
			scanParams->repetitionDelay_s * 1000.0 * ms // delay
		));
	}
	
	// End Loop Instruction
	ERROR_CATCH(spmri_mri_inst(
	  // DAC Information
		0.0, // Amplitude
		ALL_DACS, // DAC Select
		DO_WRITE, // Write
		DO_UPDATE, // Update
		DONT_CLEAR, // Clear
	  // RF Information
		0, // freq register
		0, // phase register
		0, // tx enable
		0, // phase reset
		0, // rx enable
		7, // envelope frequency register (7 = no shape)
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		loop_addr, // data
		END_LOOP, // opcode
		1.0 * us // delay
	));
	
	// Stop Instruction
	ERROR_CATCH(spmri_mri_inst(
	  // DAC Information
		0.0, // Amplitude
		ALL_DACS, // DAC Select
		DO_WRITE, // Write
		DO_UPDATE, // Update
		DONT_CLEAR, // Clear
	  // RF Information
		0, // freq register
		0, // phase register
		0, // tx enable
		0, // phase reset
		0, // rx enable
		7, // envelope frequency register (7 = no shape)
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		0, // data
		STOP, // opcode
		1.0 * us // delay
	));
	
	return 0;
}


int runScan(SCANPARAMS * scanParams)
{
	if( scanParams->verbose ) {
		printf("Scan ready to run.\n");
	}
	
	ERROR_CATCH(spmri_start());
	
	if( scanParams->verbose ) {
		printf("Scan running...\n");
	}
	
	int done = 0;
	int last_scan = 0;
	int status;
	unsigned int current_scan;
	
	// wait for scan to finish
	while( done == 0 ) {
		ERROR_CATCH(spmri_get_status(&status));
		ERROR_CATCH(spmri_get_scan_count(&current_scan));
		if( status == 0x01 ) {
			done = 1;
		} else if(current_scan != last_scan) {
			if( scanParams->verbose ) {
				printf("Current scan: %d\n", current_scan);
			}
			last_scan = current_scan;
		}
	}
	if( scanParams->verbose ) {
		printf("Scan completed.\n");
	}
	return 0;
}


int readData(SCANPARAMS * scanParams)
{
	char fid_fname[128];
	char txt_fname[128];
	char bmp_fname[128];
	int* real = malloc(scanParams->nPoints * scanParams->nPhases * sizeof(int)); 
	int* imag = malloc(scanParams->nPoints * scanParams->nPhases * sizeof(int));
	double* mag_out = malloc(scanParams->nPoints * scanParams->nPhases * sizeof(double));
	double* temp_out = malloc(scanParams->nPoints * scanParams->nPhases* sizeof(double));
	int i, j;
	double mag_out_min, mag_out_max;
	ERROR_CATCH(spmri_read_memory(real, imag, scanParams->nPoints * scanParams->nPhases));
	
	// Felix output file
	snprintf(fid_fname, 128, "%s.fid", scanParams->outputFilename);
	ERROR_CATCH(spmri_write_felix(fid_fname, "titleblock", scanParams->nPoints * scanParams->nPhases,
		scanParams->actualSpectralWidth_Hz,
		scanParams->spectrometerFrequency_MHz * 1000000.0, real, imag));
	
	// Text output file
	snprintf(txt_fname, 128, "%s.txt", scanParams->outputFilename);
	FILE* pFile = fopen( txt_fname, "w" );
	if( pFile == NULL ) return -1;
	for( j = 0 ; j < scanParams->nPoints * scanParams->nPhases ; j++ ) {
		fprintf(pFile, "%d\t%d\n", real[j], imag[j]);
	}
	fclose(pFile);
	
	// Don't continue if there is only one row of the kspace acquired
	if( scanParams->nPhases == 1 ) {
		return 0;
	}
	
	// FFTW3 Initialization
	fftw_complex *in;
	fftw_complex *out;
	fftw_plan plan;
	
	in = (fftw_complex*) fftw_malloc(scanParams->nPoints*scanParams->nPhases * sizeof(fftw_complex));
	out = (fftw_complex*) fftw_malloc(scanParams->nPoints*scanParams->nPhases * sizeof(fftw_complex));
	
	// Line broadening and input matrix filling for FFTW3
	for( i = 0 ; i < scanParams->nPhases ; i++ ) {
		for( j = 0 ; j < scanParams->nPoints ; j++ ) {
			in[i * scanParams->nPoints + j][0] = (double) real[i * scanParams->nPoints + j] * exp( -(abs(i - scanParams->nPhases/2.0) + abs(j - scanParams->nPoints/2.0))/(scanParams->nPhases/2.0 + scanParams->nPoints/2.0) * scanParams->lb_value );
			in[i * scanParams->nPoints + j][1] = (double) imag[i * scanParams->nPoints + j] * exp( -(abs(i - scanParams->nPhases/2.0) + abs(j - scanParams->nPoints/2.0))/(scanParams->nPhases/2.0 + scanParams->nPoints/2.0) * scanParams->lb_value );
		}
	}
	
	// Creating the 2DFFT plan for FFTW3
	plan = fftw_plan_dft_2d(scanParams->nPoints, scanParams->nPhases, in, out, FFTW_FORWARD, FFTW_ESTIMATE);
	
	// Executes the 2DFFT
	fftw_execute(plan);
	
	// Gets the output from the 2DFFT
	for( j = 0 ; j < scanParams->nPoints * scanParams->nPhases ; j++ ) {
		temp_out[j] = sqrt(out[j][0] * out[j][0] + out[j][1] * out[j][1]);
	}
	
	// Memory management for FFTW3
	fftw_destroy_plan(plan);
	fftw_free(in);
	fftw_free(out);
	
	// FFT shift algorithm
	int left, right, top, bottom;
	left = floor(scanParams->nPoints / 2);
	right = ceil(scanParams->nPoints / 2);
	top = floor(scanParams->nPhases / 2);
	bottom = ceil(scanParams->nPhases / 2);
	for( i = 0 ; i < scanParams->nPhases ; i++ ) {
		for( j = 0 ; j < scanParams->nPoints ; j++ ) {
			if( i < top ) {
				// top half
				if( j < left ) {
					// left half
					mag_out[i * scanParams->nPoints + j] = temp_out[(i + bottom) * scanParams->nPoints + (j + right)];
				} else {
					// right half
					mag_out[i * scanParams->nPoints + j] = temp_out[(i + bottom) * scanParams->nPoints + (j - left)];
				}
			} else {
				// bottom half
				if( j < left ) {
					// left half
					mag_out[i * scanParams->nPoints + j] = temp_out[(i - top) * scanParams->nPoints + (j + right)];
				} else {
					// right half
					mag_out[i * scanParams->nPoints + j] = temp_out[(i - top) * scanParams->nPoints + (j - left)];
				}
			}
		}
	}
	
	// Text image output file
	snprintf(txt_fname, 128, "%s_image.txt", scanParams->outputFilename);
	pFile = fopen( txt_fname, "w" );
	mag_out_min = mag_out[0];
	mag_out_max = mag_out[0];
	for( i = 0 ; i < scanParams->nPhases ; i++ ) {
		if( i != 0 ) {
			fprintf(pFile, "\n");
		}
		for( j = 0 ; j < scanParams->nPoints ; j++ ) {
			if( j != 0 ) {
				fprintf(pFile, ", ");
			}
			fprintf(pFile, "%E", mag_out[i*scanParams->nPoints + j]);
			// find min and max
			if( mag_out[i*scanParams->nPoints + j] > mag_out_max ) {
				mag_out_max = mag_out[i*scanParams->nPoints + j];
			} else if( mag_out[i*scanParams->nPoints + j] < mag_out_min ) {
				mag_out_min = mag_out[i*scanParams->nPoints + j];
			}
		}
	}
	fclose(pFile);
	
	// Colormap initialization
	COLORMAP bw_map, jet_map;
	
	// Black and white colormap
	bw_map.key_colors = 2;
	bw_map.r = malloc(2 * sizeof(char));
	bw_map.g = malloc(2 * sizeof(char));
	bw_map.b = malloc(2 * sizeof(char));
	bw_map.color = malloc(2 * sizeof(double));
	// Black
	bw_map.r[0] = 0;
	bw_map.g[0] = 0;
	bw_map.b[0] = 0;
	bw_map.color[0] = 0.0;
	// White
	bw_map.r[1] = 255;
	bw_map.g[1] = 255;
	bw_map.b[1] = 255;
	bw_map.color[1] = 1.0;
	
	// Jet colormap as used in MATLAB
	jet_map.key_colors = 6;
	jet_map.r = malloc(6 * sizeof(char));
	jet_map.g = malloc(6 * sizeof(char));
	jet_map.b = malloc(6 * sizeof(char));
	jet_map.color = malloc(6 * sizeof(double));
	// Dark blue
	jet_map.r[0] = 0;
	jet_map.g[0] = 0;
	jet_map.b[0] = 128;
	jet_map.color[0] = 0.0;
	// Blue
	jet_map.r[1] = 0;
	jet_map.g[1] = 0;
	jet_map.b[1] = 255;
	jet_map.color[1] = 0.125;
	// Indigo
	jet_map.r[2] = 0;
	jet_map.g[2] = 255;
	jet_map.b[2] = 255;
	jet_map.color[2] = 0.375;
	// Yellow
	jet_map.r[3] = 255;
	jet_map.g[3] = 255;
	jet_map.b[3] = 0;
	jet_map.color[3] = 0.625;
	// Red
	jet_map.r[4] = 255;
	jet_map.g[4] = 0;
	jet_map.b[4] = 0;
	jet_map.color[4] = 0.875;
	// Dark red
	jet_map.r[5] = 128;
	jet_map.g[5] = 0;
	jet_map.b[5] = 0;
	jet_map.color[5] = 1.0;
	
	// Initialize the BMP file for the output
	BMPFILE* bmp = malloc( sizeof( BMPFILE ) );
	double color = 0;
	unsigned char rgb_data = 0;
	
	// Color bitmap file output
	snprintf(bmp_fname, 128, "%s_color.bmp", scanParams->outputFilename);
	// Begin writing bmp file
	bmp_init_swrite(bmp, scanParams->nPhases, scanParams->nPoints, bmp_fname );
	
	while( bmp->fopen ) {
		color = (mag_out[ (bmp->current_row * bmp->num_cols) + bmp->current_column ] - mag_out_min) / (mag_out_max - mag_out_min);
		bmp_swrite_map( bmp, color, jet_map );
	}
	
	// Black and white bitmap file output
	snprintf(bmp_fname, 128, "%s_bw.bmp", scanParams->outputFilename);
	// Begin writing bmp file
	bmp_init_swrite(bmp, scanParams->nPhases, scanParams->nPoints, bmp_fname );
	
	while( bmp->fopen ) {
		color = (mag_out[ (bmp->current_row * bmp->num_cols) + bmp->current_column ] - mag_out_min) / (mag_out_max - mag_out_min);
		bmp_swrite_map( bmp, color, bw_map );
	}
	
	free(real);
	free(imag);
	free(mag_out);
	free(temp_out);
	
	return 0;
}
