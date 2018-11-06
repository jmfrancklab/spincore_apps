/*
 * Copyright (c) 2015 SpinCore Technologies, Inc.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

#include "spinapi.h"

#define CLOCK_FREQ 75.0
#define MINIMUM_PULSE_LENGTH 66.6666

// User friendly names for the control bits
#define TX_ENABLE 1
#define TX_DISABLE 0
#define PHASE_RESET 1
#define NO_PHASE_RESET 0
#define DO_TRIGGER 1
#define NO_TRIGGER 0
#define USE_SHAPE 1
#define NO_SHAPE 0

//Convert a string in the format "time units" to the proper nanosecond count value
int str_to_ns(char *str, double *time);

//Convert a nanosecond count value to the proper unit scale
const char *ns_to_units(double ns_val);
//Convert a nanosecond count value to the proper magnitude scale
double ns_to_magnitude(double ns_val);

int
main (int argc, char **argv)
{
	int start, i;
	char input_buffer[32];

	double pulse0_length, pulse0_amplitude;
	double pulse1_length, pulse1_amplitude;
	double pulse0_phase, pulse1_phase;
	double delay0, delay1;

	printf("Copyright (c) 2015 SpinCore Technologies, Inc.\n\n");
	printf("This program outputs two square pulses with amplitude, delay between pulses,\n" \
		   "and pulse lengths specified by the user.\n\n");

	printf("Pulse durations must be specified in the format: \"time units\", e.g., \"10.0 us\"\n\n");

	if (pb_init () != 0) {
		fprintf (stderr, "Error initializing board: %s\n", pb_get_error ());
		return -1;
	}

start:
	printf("\n");
	//First pulse
first_pulse_length:
	printf("Please enter the first pulse length (minimum 66.6 ns): ");

	fgets(input_buffer, sizeof(input_buffer), stdin);

	if( str_to_ns(input_buffer, &pulse0_length) ) {
		fprintf(stderr, "Invalid pulse length. Please use format: \"time units\", e.g., 10.0 us\n");
		goto first_pulse_length;
	}

	if( pulse0_length < MINIMUM_PULSE_LENGTH ) {
		fprintf(stderr, "Pulse length too short: %lf. Minimum pulse length is %lf.\n", pulse0_length, MINIMUM_PULSE_LENGTH);
		goto first_pulse_length;
	}

first_pulse_amplitude:
	printf("Please enter the first pulse amplitude scale (-1.0 to 1.0): ");

	fgets(input_buffer, sizeof(input_buffer), stdin);

	sscanf(input_buffer, "%lf", &pulse0_amplitude);

	if( pulse0_amplitude < -1.0 || pulse0_amplitude > 1.0 ) {
		fprintf(stderr, "Pulse amplitude %.2lf invalid. Amplitude scale must be between -1.0 and 1.0 inclusive.", pulse0_amplitude);
		goto first_pulse_amplitude;
	}

first_delay_length:
	printf("Please enter the delay between first and second pulses (minimum 66.6 ns): ");

	fgets(input_buffer, sizeof(input_buffer), stdin);

	if( str_to_ns(input_buffer, &delay0) ) {
		fprintf(stderr, "Invalid delay length. Please use format: \"time units\", e.g., 10.0 us\n");
		goto first_delay_length;
	}

	if( delay0 < MINIMUM_PULSE_LENGTH ) {
		fprintf(stderr, "Delay length too short: %lf. Minimum delay length is %lf.\n", delay0, MINIMUM_PULSE_LENGTH);
		goto first_delay_length;
	}

	printf("\n");

	//Second pulse
second_pulse_length:
	printf("Please enter the second pulse length (minimum 66.6 ns): ");

	fgets(input_buffer, sizeof(input_buffer), stdin);

	if( str_to_ns(input_buffer, &pulse1_length) ) {
		fprintf(stderr, "Invalid pulse length. Please use format: \"time units\", e.g., 10.0 us\n");
		goto second_pulse_length;
	}

	if( pulse1_length < MINIMUM_PULSE_LENGTH ) {
		fprintf(stderr, "Pulse length too short: %lf. Minimum pulse length is %lf.\n", pulse1_length, MINIMUM_PULSE_LENGTH);
		goto second_pulse_length;
	}

second_pulse_amplitude:
	printf("Please enter the second pulse amplitude scale (-1.0 to 1.0): ");

	fgets(input_buffer, sizeof(input_buffer), stdin);

	sscanf(input_buffer, "%lf", &pulse1_amplitude);

	if( pulse1_amplitude < -1.0 || pulse1_amplitude > 1.0 ) {
		fprintf(stderr, "Pulse amplitude %.2lf invalid. Amplitude scale must be between -1.0 and 1.0 inclusive.", pulse1_amplitude);
		goto second_pulse_amplitude;
	}

second_delay_length:
	printf("Please enter the delay between second and first pulses (minimum 66.6 ns): ");

	fgets(input_buffer, sizeof(input_buffer), stdin);

	if( str_to_ns(input_buffer, &delay1) ) {
		fprintf(stderr, "Invalid delay length. Please use format: \"time units\", e.g., 10.0 us\n");
		goto second_delay_length;
	}

	if( delay1 < MINIMUM_PULSE_LENGTH ) {
		fprintf(stderr, "Delay length too short: %lf. Minimum delay length is %lf.\n", delay1, MINIMUM_PULSE_LENGTH);
		goto second_delay_length;
	}

	printf("Pulse 0 - Amplitude: %0.2lf, Length: %0.2lf %s\n", pulse0_amplitude, ns_to_magnitude(pulse0_length), ns_to_units(pulse0_length) );
	printf("Delay 0 - Length: %0.2lf %s\n", ns_to_magnitude(delay0), ns_to_units(delay0));
	printf("Pulse 1 - Amplitude: %0.2lf, Length: %0.2lf %s\n", pulse1_amplitude, ns_to_magnitude(pulse1_length), ns_to_units(pulse1_length) );
	printf("Delay 1 - Length: %0.2lf %s\n", ns_to_magnitude(delay1), ns_to_units(delay1));
	
	pb_select_board(0); 
	pb_core_clock (CLOCK_FREQ);
	pb_set_defaults ();

	pulse0_phase = 270.0;
	if(pulse0_amplitude < 0.0) {
		pulse0_amplitude *= -1.0;
		pulse0_phase = 90.0;
	}

	pulse1_phase = 270.0;
	if(pulse1_amplitude < 0.0) {
		pulse1_amplitude *= -1.0;
		pulse1_phase = 90.0;
	}

	pb_set_amp (pulse0_amplitude, 0);
	pb_set_amp (pulse1_amplitude, 1);

	// Zero frequency is DC
	pb_start_programming (FREQ_REGS);
	pb_set_freq (0.0* MHz);
	pb_stop_programming ();

	pb_start_programming (TX_PHASE_REGS);
	pb_set_phase (pulse0_phase);
	pb_set_phase (pulse1_phase);
	pb_stop_programming ();

	pb_start_programming (PULSE_PROGRAM);
	
	//90-deg pulse
	start = pb_inst_dds_shape (0, 0, TX_ENABLE, NO_PHASE_RESET, NO_SHAPE, 0, 0x1FF, CONTINUE, 0, pulse0_length);
	pb_inst_dds_shape (0, 1, TX_DISABLE, PHASE_RESET, NO_SHAPE, 1, 0x00, CONTINUE, 0, delay0);

	//180-deg pulse
	pb_inst_dds_shape (0, 1, TX_ENABLE, NO_PHASE_RESET, NO_SHAPE, 1, 0x1FF, CONTINUE, 0, pulse1_length);
	pb_inst_dds_shape (0, 0, TX_DISABLE, PHASE_RESET, NO_SHAPE, 0, 0x0, BRANCH, start, delay1);
	pb_stop_programming ();

    pb_reset();
	pb_start ();

	printf("Program has been triggered.\n");

	goto start;

	pb_stop();

	// Release control of the board
	pb_close ();

	return 0;
}

int 
str_to_ns(char *str, double *time)
{
	double magnitude, multiplier;
	char *token, units[8];
	int ntoken = 0;

	token = strtok(str, " ");

	do {
		switch(ntoken) {
		case 0: {
				sscanf(token, "%lf", &magnitude);
			}
			break;
		case 1: {
				sscanf(token, "%s", units);
			}
			break;
		default: {
				return -1;
			}
		};

		ntoken++;

	} while( (token = strtok(NULL, " ")) != NULL);
	
	//No space between magnitude and units
	if( ntoken == 1 ) {
		sscanf(str, "%lf%2s", &magnitude, units);
	}

	multiplier = 1.0;	
	if(stricmp(units, "ns") == 0) {
		multiplier = 1.0;
	}
	else if(stricmp(units, "us") == 0) {
		multiplier = 1000.0;
	}
	else if(stricmp(units, "ms") == 0) {
		multiplier = 1000000.0;
	}
	else if(stricmp(units, "s") == 0) {
		multiplier = 1000000000.0;
	}
	else {
		return -1;
	}

	*time = (magnitude * multiplier);
	
	return 0;
}

const char *
ns_to_units(double ns_val)
{
	static char ns_string[] = "ns";
	static char us_string[] = "us";
	static char ms_string[] = "ms";
	static char s_string[] = "s";

	if(ns_val < 1000.0) {
		return ns_string;
	}
	else if( (ns_val = ns_val/1000.0) < 1000.0 ) {
		return us_string;
	}
	else if( (ns_val = ns_val/1000.0) < 1000.0 ) {
		return ms_string;
	}
	else {
		return s_string;
	}
}

double
ns_to_magnitude(double ns_val)
{
	if(ns_val < 1000.0) {
		return ns_val;
	}
	else if( (ns_val = ns_val/1000.0) < 1000.0 ) {
		return ns_val;
	}
	else if( (ns_val = ns_val/1000.0) < 1000.0 ) {
		return ns_val;
	}
	else {
		return ns_val;
	}
}
