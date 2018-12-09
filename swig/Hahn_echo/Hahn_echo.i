%module Hahn_echo
%include <windows.i>
%{
#include <windows.h>
extern char *get_time();
extern void pause(void);
extern int configureTX(int adcOffset, double carrierFreq_MHz, double tx_phase, double amplitude, unsigned int nPoints);
extern double configureRX(double SW_kHz, unsigned int nPoints, unsigned int nScans);
extern int programBoard(unsigned int nScans, double p90, double tau, double acq_time, double transient, double repetition);
extern int runBoard();
#define SWIG_FILE_WITH_INIT
extern void getData(int* output_array, int length, unsigned int nPoints, unsigned int nEchoes, char* output_name);
extern int spincore_stop(void);
%}
extern char *get_time();
extern void pause(void);
extern int configureTX(int adcOffset, double carrierFreq_MHz, double tx_phase, double amplitude, unsigned int nPoints);
extern double configureRX(double SW_kHz, unsigned int nPoints, unsigned int nScans);
extern int programBoard(unsigned int nScans, double p90, double tau, double acq_time, double transient, double repetition);
extern int runBoard();
%include "numpy.i"
%init %{
    import_array();
%}
%apply (int* ARGOUT_ARRAY1, int DIM1) {(int* output_array, int length)};
extern void getData(int* output_array, int length, unsigned int nPoints, unsigned int nEchoes, char* output_name);
extern int spincore_stop(void);
