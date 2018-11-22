#include <stdio.h>
#include <math.h>

int main(void)
{
    int vd_counter;
    float vd_step;
    int nPoints_vd;
    float p90Time_us;
    float varDelay_us;
    double temp_vd;
    vd_step = 50.;
    nPoints_vd = 8;
    p90Time_us = 0.78;
    varDelay_us = 1.0;

    for( vd_counter = 1 ; vd_counter < nPoints_vd ; vd_counter++){
        temp_vd = varDelay_us*vd_step*vd_counter;

        printf("FOR VD COUNTER = %d\n",vd_counter);
        printf("VD IS: %f\n",temp_vd);
        
    } 

    return 0;
}
