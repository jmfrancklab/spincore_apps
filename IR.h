// Based on CPMG.h
//

typedef struct SCANPARAMS
{
    // User input
    unsigned int nPoints;
    unsigned int nScans;
    unsigned int nPoints_vd;
    double SW_kHz;
    double carrierFreq_MHz;
    double amplitude;
    double p90Time_us;
    double transTime_us;
    double varDelay_us;
    double repetitionDelay_s;
    double tx_phase;
    int adcOffset;
    char* outputFilename;
    double vd_step;
    int nEchoes;
    // Derived values
    double actualSW_Hz;
    double adcFrequency_MHz;
    double acqTime_ms;
    double p180Time_us;
    double nPoints_total;
    } SCANPARAMS;

DWORD error_catch(int error, int line_number);
int processArguments(int argc, char* argv[], SCANPARAMS* scanParams);
int verifyArguments(SCANPARAMS * scanParams);
int configureBoard(SCANPARAMS * scanParams);
int programBoard(SCANPARAMS * scanParams);
int runScan(SCANPARAMS * scanParams);
int readData(SCANPARAMS * scanParams);
