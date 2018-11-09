#include <stdio.h>
#include <math.h>

#include "mrispinapi.h"

#define ERROR_CATCH(arg) error_catch(arg,__LINE__)

void pause(void)
{
    printf("Press enter to exit...");
    //flushing input stream
    fflush(stdin);
    fgetc(stdin);
}

DWORD error_catch(int error, int line_number)
{
    if( error != 0) {
        printf("ERROR CODE 0x%X AT LINE NUMBER %d\n", error, line_number);
        pause();
        exit(1);
    }
    return error;
}

int main(int argc, char *argv[])
{
    // ** Arguments **
    int nPoints = 16384;
    int nScans = 1; // 
    int nPhases = 1; // 
    double freq[1] = {14.46};
    double SW_kHz = 60.0; // from manual 
    double phase[1] = {0.0};
    double amp[1] = {1.0};
    float pulse_90 = 1.0; // us
    float pulse_180 = 2.0*pulse_90; // us
    float tau = 80.0; // us
    float delay = 40.0; //us
    int adcoffset = 38;
    char outputFilename[10] = "Hahn_Echo";

    float adcFrequency_MHz = 75.0; // need to check

    // ** Verify Arguments **
    if (nPoints > 16*1024 || nPoints < 1)
    {
        printf("Error: Maximum number of points is 16384.\n");
        return -1;
    }
    if (nScans < 1)
    {
        printf("Error: There must be at least one scan.\n");
        return -1;
    }
    if (pulse_90 < 0.065)
    {
        printf("Error: Pulse time is too small to work with board.\n");
        return -1;
    }
    if (tau < 0.065)
    {
        printf("Error: Delay time is too small to work with board.\n");
        return -1;
    }
    if (delay < 0.065)
    {
        printf("Error: Delay time is too small to work with board.\n");
        return -1;
    }
    if (amp[1] < 0 || amp[1] > 1.0)
    {
        printf("Error: Amplitude value out of range.\n");
        return -1;
    }


    // ** Configure board **
    // Initialize MRI SpinAPI
    double actual_SW;
    double SW_MHz = SW_kHz / 1000.0;
    int dec_amount;
    int i;

    ERROR_CATCH( spmri_init() );

    printf("SpinAPI initialized...\n");
    // Set all values on board to default values
    ERROR_CATCH( spmri_set_defaults() );
    // ADC offset
    ERROR_CATCH( spmri_set_adc_offset( adcoffset ) );
    // Carrier frequency registers
    ERROR_CATCH( spmri_set_frequency_registers( freq, 1 ) );
    // Phase registers
    ERROR_CATCH( spmri_set_phase_registers( phase, 1 ) );
    // Amplitude registers
    ERROR_CATCH( spmri_set_amplitude_registers( amp, 1 ) );

    ERROR_CATCH(spmri_set_num_samples(nPoints));
    ERROR_CATCH(spmri_setup_filters(
                SW_MHz, // Spectral Width in MHz
                nScans, // Number of Scans
                0, // Not Used
                &dec_amount
                ));

    actual_SW = (adcFrequency_MHz * 1e6) / (double) dec_amount;
    printf(" Decimation              : %d\n", dec_amount);
    printf("Actual Spectral Width   : %f Hz\n",
            actual_SW);

    // ** Program board **
    int loop_addr;
    printf("RPG Hahn echo test program \n\n");
    // Signal board that ready to start sending it instructions
    ERROR_CATCH( spmri_start_programming() );
    // Read current memory address for ability to return back to this point later on in prog
    ERROR_CATCH( spmri_read_addr( &loop_addr ) );

    // This instruction enables a 15 MHz analog output 90 pulse
    int start;
    start = ERROR_CATCH( spmri_mri_inst(
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
                7, // envelope freq reg (7=no shape)
                0, // amp register
                0, // cyclops phase (must be 0)
                // PulseBlaster Information
                0x01, // flags
                0, // data
                CONTINUE, // opcode
                pulse_90 * us // pulse time
                ));

    // This instruction enables delay tau
    ERROR_CATCH(spmri_mri_inst(
                // DAC Information
                0.0, // Amplitude
                ALL_DACS, // DAC Select
                DO_WRITE, // Write
                DO_UPDATE, // Update
                DONT_CLEAR, // Clear
                // RF Information
                0, // freq reg
                0, // ph reg
                0, // tx enable
                0, // phase reset
                0, // rx enable
                7, // envelope freq reg
                0, // amp register
                0, // cyclops phase
                // PulseBlaster
                0x00, // flags
                0, // data
                CONTINUE, // opcode
                tau * us // delay
                ));

    // This instruction outputs 180 pulse
   ERROR_CATCH(spmri_mri_inst(
               // DAC
               0.0, // Amplitude
               ALL_DACS, // DAC Select
               DO_WRITE, // Write
               DO_UPDATE, // Update
               DONT_CLEAR, // Clear
               // RF
               0, // freq reg
               0, // ph reg
               1, // tx enable
               0, // phase reset
               0, // rx enable
               7, // envelope freq reg
               0, // amp reg
               0, // cyclops ph
               // PulseBlaster
               0x01, // flags
               0, // data
               CONTINUE, // opcode
               pulse_180 * us // pulse length
               ));
   //
    // This instruction enables delay before acquisition
    ERROR_CATCH(spmri_mri_inst(
                // DAC Information
                0.0, // Amplitude
                ALL_DACS, // DAC Select
                DO_WRITE, // Write
                DO_UPDATE, // Update
                DONT_CLEAR, // Clear
                // RF Information
                0, // freq reg
                0, // ph reg
                0, // tx enable
                0, // phase reset
                0, // rx enable
                7, // envelope freq reg
                0, // amp register
                0, // cyclops phase
                // PulseBlaster
                0x00, // flags
                0, // data
                CONTINUE, // opcode
                delay * us // delay
                ));

   // Stop instruction
   ERROR_CATCH(spmri_mri_inst(
               // DAC
               0.0, // Amplitude
               ALL_DACS, // DAC Select
               DO_WRITE, // Write
               DO_UPDATE, // Update
               DONT_CLEAR, // Clear
               // RF
               0, // freq reg
               0, // ph reg
               0, // tx enable
               0, // ph reset
               0, // rx enable
               7, // envelope freq reg
               0, // amp reg
               0, // cyclops phase
               // PulseBlaster
               0x00, // flags
               start, // data
               STOP, // opcode
               1.0 * us // delay
               ));

   // ** Run Scan ** 
   printf("Scan ready to run.\n");

   // Starts pulse prog stored on board
   ERROR_CATCH(spmri_start());

   printf("Scan running...\n");
   
   int done = 0;
   int last_scan = 0;
   int status;
   unsigned int current_scan;

   // wait for scan to finish
   while( done == 0 ) {
       printf("Getting status...\n");
       ERROR_CATCH(spmri_get_status(&status));
       if( status == 0x01 ) {
           done = 1;
       }
       else if(current_scan != last_scan) {
            printf("Current scan: %d\n", current_scan);
       }
   }
   printf("Scan completed.\n");

   // ** Read Data **
   char txt_fname[128];
   int* real = malloc(nPoints * nPhases * sizeof(int));
   int* imag = malloc(nPoints * nPhases * sizeof(int));
   int j;
   ERROR_CATCH(spmri_read_memory(real, imag, nPoints * nPhases));

   // Write to file
   snprintf(txt_fname, 128, "%s.text", outputFilename);
   FILE* pFile = fopen( txt_fname, "w" );
   if( pFile == NULL ) return -1;
   for( j = 0 ; j < nPoints * nPhases ; j++ ) {
        fprintf(pFile, "%d\t%d\n", real[j], imag[j]);
   }
   fclose(pFile);
   printf("Data written\n");

   pause();
   // Stops the board by resetting it
   ERROR_CATCH(spmri_stop());

   return 0;
}

