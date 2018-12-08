%module Hahn_echo
%include <windows.i>
%{
#include <windows.h>
extern char *get_time();
extern void pause(void);
extern int configureTX(int adcOffset, double carrierFreq_MHz, double tx_phase, double amplitude, unsigned int nPoints);
extern double configureRX(double SW_kHz, unsigned int nPoints, unsigned int nScans);
extern int programBoard(unsigned int nScans, double p90, double tau);
extern int runBoard(double acq_time);
#define SWIG_FILE_WITH_INIT
extern int * getData(int* invec, int n, unsigned int nPoints, unsigned int nEchoes, char* output_name);
extern int spincore_stop(void);
%}
%include "numpy.i"
%init %{
    import_array();
}
extern char *get_time();
extern void pause(void);
extern int configureTX(int adcOffset, double carrierFreq_MHz, double tx_phase, double amplitude, unsigned int nPoints);
extern double configureRX(double SW_kHz, unsigned int nPoints, unsigned int nScans);
extern int programBoard(unsigned int nScans, double p90, double tau);
extern int runBoard(double acq_time);
%apply(int * INPLACE_ARRAY1, int DIM1) {(int* invec, int n)}
extern int * getData(int* invec, int n, unsigned int nPoints, unsigned int nEchoes, char* output_name);
extern int spincore_stop(void);
