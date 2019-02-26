/*
 * For time domain tuning of probe
 * outputs pulse at carrier freq in MHz for 4us
 * repeats until user stops by hitting enter
 * based on 'excite_test.c' for the RadioProcessor,
 * excite_test.c written by AB for RadioProcessor-G,
 * and references parameter set up of GradientEcho.c
 * TO COMPILE: $gcc PROGRAM_TITLE.c mrispinabi64.lib
 * TO RUN: $winpty ./a.exe
 */
#include <stdio.h>
#include <math.h>

#include "mrispinapi.h"

#define ERROR_CATCH(arg) error_catch(arg, __LINE__)

void pause(void)
{
    printf("Press enter to exit...");
    //flushing input stream
    fflush(stdin);
    fgetc(stdin);
    printf("Board cleared.");
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

    // ** Configure Board ** 
    // Initialize MRI SpinAPI
    ERROR_CATCH( spmri_init() );

    printf("SpinAPI initialized.\n");
    // Set all values on board to default values
    ERROR_CATCH( spmri_set_defaults() );

    // Carrier Frequency Registers
    double freq[1] = {14.46};
    ERROR_CATCH( spmri_set_frequency_registers( freq, 1 ) );

    // Phase Registers
    double phase[1] = {0.0};
    ERROR_CATCH( spmri_set_phase_registers( phase, 1 ) );

    // Amplitude Registers
    double amp[1] = {1.0};
    ERROR_CATCH( spmri_set_amplitude_registers( amp, 1 ) );
    
    // ** Program Board **
    printf("RPG match/tune in time domain \n\n");
    printf("FREQUENCY: %lf \n",freq[0]);
    // Signal board that ready to start sending it instructions
    ERROR_CATCH( spmri_start_programming() );
    // Read current memory address for ability to return back to this point later on in the program

    // This instruction enables analog output
    DWORD branch_addr;
    ERROR_CATCH( spmri_read_addr( &branch_addr ) );
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
        0, // phase select
        0, // rx enable
        7, // envelope frequency register (7=no shape)
        0, // amp register
        0, // cyclops phase (must be 0)
        // PulseBlaster Information
        0x00, // flags
        0, // data
        CONTINUE, // opcode
        4.0 * us // pulse time
        ));

    // This instruct disables the analog output and resets phase
    // for next instruction
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
                7, // envelope frequency register
                0, // amp register
                0, // cyclops phase
                // PulseBlaster Information
                0x00, // flags
                branch_addr, // data
                BRANCH, // opcode
                5000.0 * us // delay
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
               7, // envelope freq reg
               0, // amp register
               0, // cyclops phase
               // PulseBlaster Information
               0x00, // flags
               0, // data
               STOP, // opcode
               1.0 * us // delay
               ));

   printf("Board programmed.\n");

   // Starts the pulse program stored on board
   ERROR_CATCH(spmri_start());

   printf("Board is running...\n");

   pause();

   // Stops the board by resetting it
   ERROR_CATCH(spmri_stop());

    return 0;
}

