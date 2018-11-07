/*!\file pts_fsweep.c
 *
 * \brief This program is a simple example of using the SpinPTS API to sweep frequencies.  To use this
 * function in your own program, simply remove the main function and add this 
 * file to your project. Note that you will also need to include the header 
 * file spinpts.h and link to the dll spinpts.dll which can both be found in 
 * the main directory.
 *
 *  This program takes five arguments:
 *  pts_fsweep [Start Frequency] [End Frequency] [Increment] [Phase] (Delay)
 *  Arguments in square brackets are required. 
 *  [Start Frequency] [End Frequency] [Inncrement] are in MHz.
 *  [Phase] is in degrees.
 *  (Delay) is in milliseconds. If you do not specify a delay, a 1 second increment
 *  delay will be used by default.
 *
 * Please visit http://www.spincore.com/CD/USB-PTS/SpinPTS/Installation/
 * for more installation and use instructions.
 *
 * *****NOTE******* Currently this program does not function properly with the PTS160.
 *
 *------------------------------------------------------------------------------
 *
 *
 * *****Warning*****  Do not use clock faster than 50MHz with this board.
 *
 *
 * $Date: 2008/02/23 14:30:24 $
 *
 * To get the latest version of this code, or to contact us for support, please
 * visit http://www.spincore.com
 *
 */

/* Copyright (c) 2008 SpinCore Technologies, Inc.
 *
 * This software is provided 'as-is', without any express or implied warranty. 
 * In no event will the authors be held liable for any damages arising from the 
 * use of this software.
 *
 * Permission is granted to anyone to use this software for any purpose, 
 * including commercial applications, and to alter it and redistribute it
 * freely, subject to the following restrictions:
 *
 * 1. The origin of this software must not be misrepresented; you must not
 * claim that you wrote the original software. If you use this software in a
 * product, an acknowledgment in the product documentation would be appreciated
 * but is not required.
 * 2. Altered source versions must be plainly marked as such, and must not be
 * misrepresented as being the original software.
 * 3. This notice may not be removed or altered from any source distribution.
 */


#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <windows.h> // Use <unistd.h> for Linux

#include "spinapi.h"

void fsweep(double maxFreq, int is160, int is3200, int allowPhase, int noPTS, double fstart, double fend, double dF, double delay);
void printLicense(void);

int main()//int argc, char* argv[])
{
	double maxFreq = 250.0;
	int is160 = 0;
	int is3200 = 0;
	int allowPhase = 0;
	int noPTS = 1;
	
	double fStart;
	double fEnd;
	double dF;
	double delay;
	int quit=0;
	
	printLicense();
    printf ("USB Interface to PTS Synthesizer developed by SpinCore Technologies\n\n");
    printf ("Using spinapi library version %s\n", pb_get_version ());
    printf("\nPTS Frequency Sweep: Start Frequency, End Frequency, Increment, Phase, Delay\n");

    printf("\nPlease enter the desired starting frequency (MHz) (Enter 0 to exit): ");
    scanf("%lf", &fStart);
    if(fStart==0)
    {
        quit=1;
    }
    else
    {
        printf("\nPlease enter the desired ending frequency (MHz): ");
        scanf("%lf", &fEnd);
        printf("\nPlease enter the desired frequency increment (MHz): ");
        scanf("%lf", &dF);
        printf("\nPlease enter the desired delay (ms): ");
        scanf("%lf", &delay);
        printf("\nYou must close the window to stop the program.");
        while(1){
    	   fsweep(maxFreq, is160, is3200, allowPhase, noPTS, fStart, fEnd, dF, delay);
        }
		return 0;
    }
	return 0;
}
	
void fsweep(double maxFreq, int is160, int is3200, int allowPhase, int noPTS, double fstart, double fend, double dF, double delay)
{
	int i;
	int count;
	
	if(dF == 0.0 || fstart == fend)
	{
		set_pts(maxFreq, is160, is3200, allowPhase, noPTS, fstart, 0);
	}
	
	count = fabs( (fstart - fend) / dF );
	
	if(fstart > fend && dF > 0.0)  //Force proper increment sign.
		dF = -dF;
	else if(fstart < fend && dF < 0.0)
		dF = -dF;
	
	
	
	for(i=0; i <= count; ++i)
	{
		set_pts(maxFreq, is160, is3200, allowPhase, noPTS, fstart+i*dF, 0);
		if(delay>=1000)
        {
            printf("changed to %lf", fstart+i*dF);
            printf(" MHz\n");
        }

		Sleep(delay);

	}
	
	
	
}
		
void printLicense(void)
{
     printf("Copyright (c) 2009 SpinCore Technologies, Inc.\n");
     printf(" http://www.spincore.com\n\n");
     printf("This software is provided 'as-is', without any express or implied warranty.\n");
     printf("In no event will the authors be held liable for any damages arising from the\n"); 
     printf("use of this software.\n");
     printf("\n");
     printf("Permission is granted to anyone to use this software for any purpose,\n");
     printf("including commercial applications, and to alter it and redistribute it\n");
     printf("freely, subject to the following restrictions:\n");
     printf("\n");
     printf("1. The origin of this software must not be misrepresented; you must not\n");
     printf("claim that you wrote the original software. If you use this software in a\n");
     printf("product, an acknowledgment in the product documentation would be appreciated\n");
     printf("but is not required.\n");
     printf("2. Altered source versions must be plainly marked as such, and must not be\n");
     printf("misrepresented as being the original software.\n");
     printf("3. This notice may not be removed or altered from any source distribution.\n\n");
     system("pause");
     system("cls");
     return;
}	
