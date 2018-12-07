%module Hahn_echo
%include <windows.i>
%{
#include <windows.h>
extern char *get_time();
extern void pause(void);
extern int configureBoard(int adcOffset, double carrierFreq_MHz, double tx_phase, double amplitude);
extern int programBoard(int nScans, double p90, double tau);
extern int runBoard();
extern int spincore_stop(void);
%}
extern char *get_time();
extern void pause(void);
extern int configureBoard(int adcOffset, double carrierFreq_MHz, double tx_phase, double amplitude);
extern int programBoard(int nScans, double p90, double tau);
extern int runBoard();
extern int spincore_stop(void);
