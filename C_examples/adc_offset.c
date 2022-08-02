#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#include "mrispinapi.h"

#define NUM_POINTS (16*1024)
#define SW_MHZ (75.0/1.0)
#define SF_MHZ (0.0)

#define ADC_OFFSET_MIN -256
#define ADC_OFFSET_MAX 256

#define ERROR_CATCH(arg) error_catch(arg, __LINE__)

double get_dc_value(int adc_offset);
int configureBoard(int adc_offset);
int programBoard( );
int runScan( );
int readData(int adc_offset, double* peak);,
int ppg_element(char *str_label, double firstarg, int secondarg); // this comes from SpinCore_pp/SpinCore_pp.c

DWORD error_catch(int error, int line_number)
{
	if( error != 0 ) {
		printf("ERROR CODE 0x%X AT LINE NUMBER %d\n", error, line_number);
		exit(1);
	}
	return error;
}


int main(int argc, char *argv[])
{
	double max_offset_result = get_dc_value(ADC_OFFSET_MAX);
	double min_offset_result = get_dc_value(ADC_OFFSET_MIN);


    if(max_offset_result==0 && min_offset_result==0){
        printf("both max and min offset results are 0 -- try using an adc offset of 0\n");
        return 0;
    }
	
	double theoretical_adc_offset = (0 - min_offset_result) / (max_offset_result - min_offset_result) * (ADC_OFFSET_MAX - ADC_OFFSET_MIN) + ADC_OFFSET_MIN;
	int test_offset = round( theoretical_adc_offset );
	
	printf("Correct ADC offset = %d\n", test_offset);
	
	return 0;
}

double get_dc_value(int adc_offset)
{
	double peak;
	ERROR_CATCH( configureBoard( adc_offset ) );
	ERROR_CATCH( programBoard( ) );
	ERROR_CATCH( runScan( ) );
	ERROR_CATCH( readData( adc_offset, &peak ) );
	return peak;
}

int configureBoard(int adc_offset)
{
	int dec_amount;
	
	ERROR_CATCH( spmri_init() );
	ERROR_CATCH( spmri_set_defaults() );
	ERROR_CATCH( spmri_stop() );
	
	// ADC offset
	ERROR_CATCH( spmri_set_adc_offset( adc_offset ) );
	
	ERROR_CATCH( spmri_set_num_samples( NUM_POINTS ) );
	
	ERROR_CATCH(spmri_setup_filters(
		SW_MHZ, // Spectral Width in MHz
		1, // Number of Scans
		0, // Not Used
		&dec_amount
	));
	
	// Carrier Frequency Registers
	double freqs[1] = {SF_MHZ}; // MHz
	ERROR_CATCH(spmri_set_frequency_registers( freqs, 1 ));
	
	return 0;
}

int programBoard( )
{
    ERROR_CATCH(spmri_start_programming());
    ppg_element("delay", 1.0, 0);
    ERROR_CATCH;
    double acq_time_us = NUM_POINTS / (SW_MHZ);
    ppg_element("acquire", acq_time_us*us/ms, 0);
    /*here*/
    stop_ppg();
    return 0;
}

int runBoard()
{
	ERROR_CATCH(spmri_start());
	
	int done = 0;
	int status;
	
	// wait for scan to finish
	while( done == 0 )
    {
		ERROR_CATCH(spmri_get_status(&status));
		if( status == 0x01 ) {
			done = 1;
		}
	}
	
	return 0;
}

int readData(int adc_offset, double* peak)
{
	int i;
	int real[NUM_POINTS];
	int imag[NUM_POINTS];
	double mag_out[NUM_POINTS];
	double mag_out_max;
	int mag_out_max_index;
	double dc_value;
	
	ERROR_CATCH(spmri_read_memory(real, imag, NUM_POINTS));
	
	dc_value = 0;
	for( i = 0 ; i < NUM_POINTS ; i++ ) {
        //printf("for adc offset %d, point %d, I get %d\n",adc_offset,i,real[i]);
		dc_value += real[i];
	}
	
	// Felix output file
	char filename[128];
	snprintf(filename, 128, "adc_offest_%d.fid", adc_offset);
	ERROR_CATCH(spmri_write_felix(filename, "titleblock", NUM_POINTS,
		SW_MHZ * 1e6, SF_MHZ * 1e6 + 1e-6, real, imag));
	
	// DC frequency
	*peak = dc_value;
	
	return 0;
}
