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

/*
 * Example Program 2
 * SpinCore Technologies Inc.
 * 2011
 *
 * This program outputs a pattern on the three gradient channels.
 */
 

#include <stdio.h>

#include "mrispinapi.h"

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
	int loop_addr;
	
	printf("Example 2 - SpinCore Technologies 2011\n\n");
	printf("This program outputs a pattern on the three gradient channels.\n\n");
	
	// Initializes MRI SpinAPI
	ERROR_CATCH( spmri_init() );
	
	printf("SpinAPI initialized.\n");
	
	// Sets all of the values related to the board to their default values
	ERROR_CATCH( spmri_set_defaults() );
	
	// Signals to the board that you are going to start programming instructions
	// to it. The board resets the address in preperation.
	ERROR_CATCH( spmri_start_programming() );
	
	// Reads the current address in instruction memory for the branch
	// instruction later on that will return to this point in the program.
	ERROR_CATCH( spmri_read_addr( &loop_addr ) );
	
	
	// This instruction clears all of the DACs and sets the slice DAC to 1.0.
	ERROR_CATCH(spmri_mri_inst(
	  // DAC Information
		1.0, // Amplitude
		SLICE_DAC, // DAC Select
		DO_WRITE, // Write
		DO_UPDATE, // Update
		DO_CLEAR, // Clear
	  // RF Information
		0, // freq register
		0, // phase register
		0, // tx enable
		0, // phase reset
		0, // rx enable
		0, // envelope frequency register
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		0, // data
		CONTINUE, // opcode
		200.0 * ms // delay
	));
	
	// This instruction keeps all of the DACs output the same except for the
	// phase DAC.  The phase DAC is set to 1.0.
	ERROR_CATCH(spmri_mri_inst(
	  // DAC Information
		1.0, // Amplitude
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
		0, // envelope frequency register
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		0, // data
		CONTINUE, // opcode
		100.0 * ms // delay
	));
	
	// This instruction keeps all of the DACs output the same except for the
	// freq DAC.  The freq DAC is set to 1.0.
	ERROR_CATCH(spmri_mri_inst(
	  // DAC Information
		1.0, // Amplitude
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
		0, // envelope frequency register
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		0, // data
		CONTINUE, // opcode
		100.0 * ms // delay
	));
	
	// This instruction clears all of the DACs and sets the slice DAC to -1.0.
	// The same process above repeats except for amplitudes of -1.0 instead of
	// 1.0.
	ERROR_CATCH(spmri_mri_inst(
	  // DAC Information
		-1.0, // Amplitude
		SLICE_DAC, // DAC Select
		DO_WRITE, // Write
		DO_UPDATE, // Update
		DO_CLEAR, // Clear
	  // RF Information
		0, // freq register
		0, // phase register
		0, // tx enable
		0, // phase reset
		0, // rx enable
		0, // envelope frequency register
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		0, // data
		CONTINUE, // opcode
		200.0 * ms // delay
	));
	
	ERROR_CATCH(spmri_mri_inst(
	  // DAC Information
		-1.0, // Amplitude
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
		0, // envelope frequency register
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		0, // data
		CONTINUE, // opcode
		100.0 * ms // delay
	));
	
	ERROR_CATCH(spmri_mri_inst(
	  // DAC Information
		-1.0, // Amplitude
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
		0, // envelope frequency register
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		0, // data
		CONTINUE, // opcode
		100.0 * ms // delay
	));
	
	// These next 4 instructions bring the amplitude of all of the gradients
	// from 0.0 to -1.0 in four levels: -0.0, -0.33, -0.67, and -1.0.
	// Each instruction lasts for 100 ms.
	// The last instruction loops back to the first instruction.
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
		0, // envelope frequency register
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		0, // data
		CONTINUE, // opcode
		100.0 * ms // delay
	));
	
	ERROR_CATCH(spmri_mri_inst(
	  // DAC Information
		-0.33, // Amplitude
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
		0, // envelope frequency register
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		0, // data
		CONTINUE, // opcode
		100.0 * ms // delay
	));
	
	ERROR_CATCH(spmri_mri_inst(
	  // DAC Information
		-0.67, // Amplitude
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
		0, // envelope frequency register
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		0, // data
		CONTINUE, // opcode
		100.0 * ms // delay
	));
	
	ERROR_CATCH(spmri_mri_inst(
	  // DAC Information
		-1.0, // Amplitude
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
		0, // envelope frequency register
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		loop_addr, // data
		BRANCH, // opcode
		100.0 * ms // delay
	));
	
	printf("Board programmed.\n");
	
	// Starts the pulse program stored on the board
	ERROR_CATCH(spmri_start());
	
	printf("Board is running...\n");
	
	pause();
	
	// Stops the board by resetting it.
	ERROR_CATCH(spmri_stop());
	
	// This programs a small pulse program to the board to clear the DACs
	// Without this program, the DACs would keep their output when stopped.
	ERROR_CATCH( spmri_start_programming() );
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
		0, // envelope frequency register
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		0, // data
		CONTINUE, // opcode
		100.0 * ms // delay
	));
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
		0, // tx enable
		0, // phase reset
		0, // rx enable
		0, // envelope frequency register
		0, // amp register
		0, // cyclops phase
	  // Pulse Blaster Information
		0x00, // flags
		0, // data
		STOP, // opcode
		100.0 * ms // delay
	));
	// Runs the program to clear the DACs
	ERROR_CATCH(spmri_start());
	// This is more than enough time to reprogram the board's DACs
	ERROR_CATCH(spmri_stop());
	
	return 0;
}
