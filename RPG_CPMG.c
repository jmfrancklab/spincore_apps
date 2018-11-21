#include <stdio.h>
#include <math.h>

#include "mrispinapi.h"
#include "CPMG.h"

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
    SCANPARAMS myScan;

    ERROR_CATCH( processArguments(argc, argv, &myScan) );
    ERROR_CATCH( verifyArguments( &myScan ) );
    ERROR_CATCH( configureBoard( &myScan ) );
    ERROR_CATCH( programBoard( & myScan ) );
    ERROR_CATCH( runScan( &myScan ) );
    ERROR_CATCH( readData( &myScan ) );
    printf("Program complete\n");
    pause();
    ERROR_CATCH( spmri_stop());

    return 0;

    }

int processArguments(int argc, char* argv[], SCANPARAMS* scanParams)
{

    scanParams->nPoints = atoi (argv[1]);
    scanParams->nScans = atoi (argv[2]);
    scanParams->nEchoes = atoi (argv[3]);
    scanParams->SW_kHz = atof (argv[4]);
    scanParams->carrierFreq_MHz = atof (argv[5]);
    scanParams->amplitude = atof (argv[6]);
    scanParams->p90Time_us = atof (argv[7]);
    scanParams->transTime_us = atof (argv[8]);
    scanParams->tauDelay_us = atof (argv[9]);
    scanParams->repetitionDelay_s = atof(argv[10]);
    scanParams->tx_phase = atof (argv[11]);
    scanParams->adcOffset = atoi (argv[12]);
    scanParams->outputFilename = argv[13];
    
    scanParams->adcFrequency_MHz = 75.0;
    scanParams->p180Time_us = (scanParams->p90Time_us * 2.0);

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
    double phases[1] = {scanParams->tx_phase};
    ERROR_CATCH(spmri_set_phase_registers( phases, 1 ));

    // Set Amplitude registers
    double amps[1] = {scanParams->amplitude};
    ERROR_CATCH(spmri_set_amplitude_registers( amps, 1 ));

    // Set Acquisition parameters
    scanParams->nPoints = roundUpPower2(scanParams->nPoints); // make sure acquired number of points
                                        // can be stored by the board
    ERROR_CATCH(spmri_set_num_samples(scanParams->nPoints));
    scanParams->nPoints_total = scanParams->nEchoes * scanParams->nPoints;
    if(scanParams->nPoints_total > 16384){
        printf("WARNING: Trying to acquire too many points than board can store.\n");
                }
    ERROR_CATCH(spmri_setup_filters(
                SW_MHz, // SW in Mhz
                scanParams->nScans, // Number of Scacns
                0, // Not used?
                &dec_amount
                ));

    actual_SW = (scanParams->adcFrequency_MHz * 1e6) / (double) dec_amount;
    scanParams->actualSW_Hz = actual_SW;

    printf("Decimation: %d\n", dec_amount);
    printf("Actual SW: %f Hz\n", scanParams->actualSW_Hz);
    
    scanParams->acqTime_ms = scanParams->nPoints / actual_SW * 1000.0;

    ERROR_CATCH(spmri_set_num_segments(scanParams->nEchoes));
    return 0;
}

int programBoard(SCANPARAMS * scanParams)
{
    DWORD loop_addr;
    DWORD scan_loop_label;
    DWORD echo_loop_label;
    ERROR_CATCH(spmri_start_programming());
    ERROR_CATCH( spmri_read_addr( &loop_addr ) );

    // SCAN LOOP
    ERROR_CATCH( spmri_read_addr( &scan_loop_label ) );
    ERROR_CATCH(spmri_mri_inst(
                // DAC
                0.0, // Amplitude
                ALL_DACS, // DAC Select
                DO_WRITE, // Write
                DO_UPDATE, // Update
                DONT_CLEAR, // Clear
                // RF
                0, // freq reg
                0, // phase reg
                0, // tx enable
                1, // phase reset
                0, // rx enable
                7, // envelope freq (default)
                0, // amp reg
                0, // cyclops (default)
                // PulseBlaster
                0x00, // flags = TTL low (off)
                scanParams->nScans, // data
                LOOP, // opcode
                1.0 * us // delay
                ));

        // PHASE RESET TRANSIENT DELAY
        // *** NEED THIS OR ELSE GET STRANGE LOW FREQ *** //
        // *** ARTIFACT AT BEGINNING OF FIRST PULSE   *** // 
        ERROR_CATCH(spmri_mri_inst(
                    // DAC
                    0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                    // RF
                    0,0,0,0,0,7,0,0,
                    // PB
                    0x00,0,CONTINUE,1.0*us));
    // 90 PULSE
    ERROR_CATCH(spmri_mri_inst(
                // DAC
                0.0,ALL_DACS,DONT_WRITE,DONT_UPDATE,DONT_CLEAR,
                // RF
                0,0,1,0,0,7,0,0,
                // PB
                0x00,0,CONTINUE,scanParams->p90Time_us*us
                ));
    // TAU DELAY
    ERROR_CATCH(spmri_mri_inst(
                // DAC
                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                // RF
                0,0,0,0,0,7,0,0,
                // PB
                0x00,
                0,
                CONTINUE,
                scanParams->tauDelay_us*0.5*us));
    // 180 PULSE
    ERROR_CATCH( spmri_read_addr( &echo_loop_label ) );
    //echo_loop_label = 
    ERROR_CATCH(spmri_mri_inst(
                // DAC
                0.0,ALL_DACS,DONT_WRITE,DONT_UPDATE,DONT_CLEAR,
                // RF
                0,0,1,0,0,7,0,0,
                // PB
                0x00,scanParams->nEchoes,LOOP,scanParams->p180Time_us*us
                ));
    // TRANSIENT DELAY
    ERROR_CATCH(spmri_mri_inst(
                // DAC
                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                // RF
                0,0,0,0,0,7,0,0,
                // PB
                0x00,0,CONTINUE,scanParams->transTime_us * us
                ));
    // DATA ACQUISITION (ALSO SPECIFIES END OF ECHO LOOP)
    ERROR_CATCH(spmri_mri_inst(
                // DAC
                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                // RF
                0,0,0,0,1,7,0,0,
                // PB
                0x00,echo_loop_label,END_LOOP,scanParams->acqTime_ms * ms
                ));
    // REPETITION DELAY (ALSO SPECIFIED END OF SCAN LOOP)
    ERROR_CATCH(spmri_mri_inst(
                // DAC
                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                // RF
                0,0,0,0,0,7,0,0,
                // PB
                0x00,scan_loop_label,END_LOOP,scanParams->repetitionDelay_s * 1000.0 * ms
                ));
    // STOP
    ERROR_CATCH(spmri_mri_inst(
                // DAC
                0.0,ALL_DACS,DO_WRITE,DO_UPDATE,DONT_CLEAR,
                // RF
                0,0,0,0,0,7,0,0,
                // PB
                0x00,0,STOP,1.0 * us
                ));

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
    int* real = malloc(scanParams->nPoints * scanParams->nEchoes * sizeof(int));
    int* imag = malloc(scanParams->nPoints * scanParams->nEchoes * sizeof(int));
    int j;
    ERROR_CATCH(spmri_read_memory(real, imag, scanParams->nPoints * scanParams->nEchoes));
    // Text file output
    snprintf(txt_fname, 128, "%s.txt", scanParams->outputFilename);
    FILE* pFile = fopen( txt_fname, "w" );
    if ( pFile == NULL ) return -1;
    fprintf(pFile, "SPECTRAL WIDTH %f\n", scanParams->actualSW_Hz);
    for( j = 0 ; j < scanParams->nPoints * scanParams->nEchoes ; j++)
    {
        fprintf(pFile, "%d\t%d\n", real[j], imag[j]);
    }
    fclose(pFile);
    printf("Data written\n");
    return 0;
}

// Function to round up acquired points to highest power of 2
// From CPMG sequence by Sleator
int roundUpPower2(int number)
{
    int remainder_total = 0;
    int rounded_number = 1;
    while(number != 0){
        remainder_total += number % 2;
        number /= 2;
        rounded_number *= 2;
    }
    if(remainder_total == 1){
        rounded_number /= 2;
    }
    
    return rounded_number;
}
