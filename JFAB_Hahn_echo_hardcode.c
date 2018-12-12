#include <stdio.h>
#include <string.h>
#include <math.h>

#include "mrispinapi.h"
// This was defined in Hahn_echo.h, but I want one file that's self-contained.
// All parameters are defined at the beginning of main()
typedef struct SCANPARAMS
{
    // User input
    unsigned int nPoints;
    unsigned int nScans;
    unsigned int nPhases;
    double SW_kHz;
    double carrierFreq_MHz;
    double amplitude;
    double p90Time_us;
    double transTime_us;
    double tauDelay_us;
    double repetitionDelay_s;
    double phase_values[4];
    unsigned int phase90_idx;
    unsigned int phase180_idx;
    int adcOffset;
    char outputFilename[128];
    // Derived values
    double actualSW_Hz;
    double adcFrequency_MHz;
    double acqTime_ms;
    double p180Time_us;
    } SCANPARAMS;

/*for testing purposes here we write a self-contained function for a spin echo,
 * where all parameters are hard-coded into this file*/

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

int processArguments(int argc, char* argv[], SCANPARAMS* scanParams)
{


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

	if (scanParams->p90Time_us < 0.065)
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
	
	return 0;
}

int configureBoard(SCANPARAMS * scanParams)
{
    double actual_SW; // Hz
    double SW_MHz = scanParams->SW_kHz / 1000.0;
    int dec_amount;
    int i;

    ERROR_CATCH( spmri_init() );
    ERROR_CATCH( spmri_set_defaults() );
    
    // Set ADC offset
    ERROR_CATCH( spmri_set_adc_offset( scanParams->adcOffset ) );

    // Set Carrier Frequency
    double freqs[1] = {scanParams->carrierFreq_MHz}; // Mhz
    ERROR_CATCH(spmri_set_frequency_registers( freqs, 1));

    // Set Phase registers
    ERROR_CATCH(spmri_set_phase_registers( scanParams->phase_values, 4 ));

    // Set Amplitude registers
    double amps[1] = {scanParams->amplitude};
    ERROR_CATCH(spmri_set_amplitude_registers( amps, 1 ));

    // Set Acquisition parameters
    ERROR_CATCH(spmri_set_num_samples(scanParams->nPoints));
    ERROR_CATCH(spmri_setup_filters(
                SW_MHz, // SW in Mhz
                scanParams->nScans, // Number of Scacns
                0, // Not used?
                &dec_amount
                ));
    //ERROR_CATCH(spmri_set_num_segments(scanParams->nPhases));

    actual_SW = (scanParams->adcFrequency_MHz * 1e6) / (double) dec_amount;
    scanParams->actualSW_Hz = actual_SW;

    printf("Decimation: %d\n", dec_amount);
    printf("Actual SW: %f Hz\n", scanParams->actualSW_Hz);
    
    scanParams->acqTime_ms = scanParams->nPoints / actual_SW * 1000.0;

    return 0;
}

int programBoard(SCANPARAMS * scanParams)
{
    DWORD loop_addr[1];// write it this way so that we can easily expand to multiple loops
    ERROR_CATCH(spmri_start_programming());
    // {{{ start of loop
    ERROR_CATCH( spmri_read_addr( &loop_addr[0] ) );
    ERROR_CATCH(spmri_mri_inst(
                // -- DAC section --
                0.0, // Amplitude
                ALL_DACS, // DAC Select
                DO_WRITE, // Write
                DO_UPDATE, // Update
                DONT_CLEAR, // Clear
                // --- RF section --
                0, // freq register
                0, // phase register
                0, // tx enable
                0, // phase reset
                0, // rx enable
                7, // envelope freq (default)
                0, // amp register
                0, // cyclops (default)
                // -- PulseBlaster section --
                0x00, // flags = TTL low (off)
                scanParams->nScans, // data
                LOOP, // opcode -- listed in radioprocessor g manual
                1.0 * us // delay
                ));
    // }}}

    //    // PHASE RESET TRANSIENT DELAY
    //    // *** NEED THIS OR ELSE GET STRANGE LOW FREQ *** //
    //    // *** ARTIFACT AT BEGINNING OF FIRST PULSE   *** // 
    //    ERROR_CATCH(spmri_mri_inst(
    //                // DAC
    //                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
    //                // RF
    //                0,0,0,0,0,7,0,0,
    //                // PB
    //                0x00,0,CONTINUE,1.0*us));
    // {{{ 90 PULSE
    ERROR_CATCH(spmri_mri_inst(
                // DAC: Amplitude, DAC Select, Write, Update, Clear
                0.0,ALL_DACS,DONT_WRITE,DONT_UPDATE,DONT_CLEAR,
                // RF: freq register, phase register, tx enable, phase reset, rx enable, envelope freq (default), amp register, cyclops (default),
                0,scanParams->phase90_idx,1,0,0,7,0,0,
                // PB: flags = TTL low (off), data, opcode -- listed in radioprocessor g manual, delay
                0x00,0,CONTINUE,scanParams->p90Time_us*us
                ));
    // }}}
    // {{{ TAU DELAY
    ERROR_CATCH(spmri_mri_inst(
                // DAC: Amplitude, DAC Select, Write, Update, Clear
                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                // RF: freq register, phase register, tx enable, phase reset, rx enable, envelope freq (default), amp register, cyclops (default),
                0,0,0,0,0,7,0,0,
                // PB: flags = TTL low (off), data, opcode -- listed in radioprocessor g manual, delay
                0x00, 0, CONTINUE, scanParams->tauDelay_us*us));
    // }}}
    // {{{ 180 PULSE
    ERROR_CATCH(spmri_mri_inst(
                // DAC: Amplitude, DAC Select, Write, Update, Clear
                0.0,ALL_DACS,DONT_WRITE,DONT_UPDATE,DONT_CLEAR,
                // RF: freq register, phase register, tx enable, phase reset, rx enable, envelope freq (default), amp register, cyclops (default),
                0,scanParams->phase180_idx,1,0,0,7,0,0,
                // PB: flags = TTL low (off), data, opcode -- listed in radioprocessor g manual, delay
                0x00,0,CONTINUE,scanParams->p180Time_us*us
                ));
    // }}}
    // {{{ TRANSIENT DELAY
    ERROR_CATCH(spmri_mri_inst(
                // DAC: Amplitude, DAC Select, Write, Update, Clear
                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                // RF: freq register, phase register, tx enable, phase reset, rx enable, envelope freq (default), amp register, cyclops (default),
                0,0,0,0,0,7,0,0,
                // PB: flags = TTL low (off), data, opcode -- listed in radioprocessor g manual, delay
                0x00,0,CONTINUE,scanParams->transTime_us * us
                ));
    // }}}
    // {{{ DATA ACQUISITION
    ERROR_CATCH(spmri_mri_inst(
                // DAC: Amplitude, DAC Select, Write, Update, Clear
                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                // RF: freq register, phase register, tx enable, phase reset, rx enable, envelope freq (default), amp register, cyclops (default),
                0,0,0,0,1,7,0,0,
                // PB: flags = TTL low (off), data, opcode -- listed in radioprocessor g manual, delay
                0x00,0,CONTINUE,scanParams->acqTime_ms * ms
                ));
    // }}}
    // {{{ REPETITION DELAY
    ERROR_CATCH(spmri_mri_inst(
                // DAC: Amplitude, DAC Select, Write, Update, Clear
                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                // RF: freq register, phase register, tx enable, phase reset, rx enable, envelope freq (default), amp register, cyclops (default),
                0,0,0,0,0,7,0,0,
                // PB: flags = TTL low (off), data, opcode -- listed in radioprocessor g manual, delay
                0x00,0,CONTINUE,scanParams->repetitionDelay_s * 1000.0 * ms
                ));
    // }}}
    // {{{ END LOOP
    ERROR_CATCH(spmri_mri_inst(
                // DAC
                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                // RF
                0,0,0,0,0,7,0,0,
                // PB
                0x00,loop_addr[0],END_LOOP,1.0 * us
                ));
    // }}}
    // {{{ STOP
    ERROR_CATCH(spmri_mri_inst(
                // DAC
                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                // RF
                0,0,0,0,0,7,0,0,
                // PB
                0x00,0,STOP,1.0 * us
                ));
    // }}}
    return 0;
}

int runScan(SCANPARAMS * scanParams)
{
    printf("Scan ready to run.\n");
    ERROR_CATCH(spmri_start());

    printf("Scan running...\n");

    int done = 0;
    int last_scan = 0;
    int status;
    unsigned int current_scan;

    // wait for scan to finish
    while( done == 0)
    {
        ERROR_CATCH(spmri_get_status(&status));
        ERROR_CATCH(spmri_get_scan_count(&current_scan));
        if( status == 0x01 ) {
            done = 1; }
        else if(current_scan != last_scan) {
            printf("Current scan: %d\n", current_scan);
            last_scan = current_scan;
        }
    }
    printf("Scan completed.\n");

    return 0;
}

int readData(SCANPARAMS * scanParams)
{
    char txt_fname[128];
    int* real = malloc(scanParams->nPoints * scanParams->nPhases * sizeof(int));
    int* imag = malloc(scanParams->nPoints * scanParams->nPhases * sizeof(int));
    int j;
    ERROR_CATCH(spmri_read_memory(real, imag, scanParams->nPoints * scanParams->nPhases));
    // Text file output
    //snprintf(txt_fname, 128, "%s.txt", scanParams->outputFilename);
    snprintf(txt_fname, 128, "diagnostic_run.txt");
    FILE* pFile = fopen( txt_fname, "w" );
    if ( pFile == NULL ) return -1;
    fprintf(pFile, "SPECTRAL WIDTH %f\n", scanParams->actualSW_Hz);
    for( j = 0 ; j < scanParams->nPoints * scanParams->nPhases ; j++)
    {
        fprintf(pFile, "%d\t%d\n", real[j], imag[j]);
    }
    fclose(pFile);
    printf("Data written\n");
    return 0;
}

int main(int argc, char *argv[])
{
    SCANPARAMS scanParams_object;
    SCANPARAMS *scanParams;
    scanParams = &scanParams_object;
    //char myfile[128] = "diagnostic_run";
    //strcpy(scanParams->outputFilename,"diagnostic_run");
    // ==================
    // Acquisition
    // ==================
    scanParams->nPoints=(int) 16384;
    scanParams->nScans=(int) 4;
    scanParams->nPhases=(int) 1;
    scanParams->SW_kHz=(float) 200.0;
    // ==================;
    // Excitation;
    // ==================;
    scanParams->carrierFreq_MHz=(float) 14.46;
    scanParams->amplitude=(float) 1.0;
    scanParams->p90Time_us=(float) 1.0;
    // ==================;
    // Delays;
    // ==================;
    scanParams->transTime_us=(float) 500.0;
    scanParams->tauDelay_us=(float) 10500.0;
    scanParams->repetitionDelay_s=(float) 1.0;

    scanParams->phase_values[0] = 0.0;
    scanParams->phase_values[1] = 90.0;
    scanParams->phase_values[2] = 180.0;
    scanParams->phase_values[3] = 270.0;
    scanParams->phase90_idx=(unsigned int)0;//set the phase of the 90 -- 0,1,2,3, or 4
    scanParams->phase180_idx=(unsigned int)0;//set the phase of the 180 -- 0,1,2,3, or 4

    scanParams->adcOffset=(float) 47;
    
    scanParams->adcFrequency_MHz = 75.0;
    scanParams->p180Time_us = (scanParams->p90Time_us * 2.0);

    ERROR_CATCH( verifyArguments( scanParams ) );
    ERROR_CATCH( configureBoard( scanParams ) );
    ERROR_CATCH( programBoard( scanParams ) );
    ERROR_CATCH( runScan( scanParams ) );
    ERROR_CATCH( readData( scanParams ) );
    ERROR_CATCH( spmri_stop());

    return 0;
}

