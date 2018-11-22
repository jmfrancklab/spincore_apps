#include <stdio.h>
#include <math.h>

int main(void)
{
    int nutation_counter;
    float nutation_step;
    int nPoints_nutation;
    float p90Time_us;
    float tauDelay_us;
    double temp_90;
    double temp_tau;
    double temp_180;
    nutation_step = 1.0;
    nPoints_nutation = 64;
    p90Time_us = 0.065;
    tauDelay_us = 2500.0;

    //EXPRESSIONS 
    // PW_90 = p90 + nut_step*nut_counter
    // TAU = tau*0.5 - (2*nut_counter*nut_step)
    // PW_180 = (2*(p90+nut_step*nut_counter))
    for( nutation_counter = 1 ; nutation_counter < nPoints_nutation ; nutation_counter++){
        temp_90 = p90Time_us * nutation_step*nutation_counter;
        //temp_tau = tauDelay_us*0.5 - 2.0*nutation_counter*nutation_step;
        //temp_180 = 2.0*(p90Time_us + nutation_step*nutation_counter);

        printf("FOR NUTATION COUNTER = %d\n",nutation_counter);
        printf("90 TIME IS: %f\n",temp_90);
            //TAU TIME IS: %f\n180 TIME IS: %f\n",temp_90,temp_tau,temp_180);
        
    } 

    return 0;
}
