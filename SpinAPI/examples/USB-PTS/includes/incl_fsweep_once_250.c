/*!\file incl_fsweep_once_250.c
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

/* Copyright (c) 2009 SpinCore Technologies, Inc.
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


#include <windows.h>  // Use <unistd.h> for Linux
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#include "spinapi.h"


void usage(char* argv[]); 
int fsweep(double maxFreq, int is160, int is3200, int allowPhase, int noPTS, double fstart, double fend, double dF, double delay);

int main(int argc, char* argv[])
{
	double maxFreq = 250;
	int is160 = 0;
	int is3200 = 0;
	int allowPhase = 0;
	int noPTS = 1;
	
	double fStart;
	double fEnd;
	double dF;
	double delay;
	
	if(!(argc == 5 || argc == 6))
	{
		usage( argv );
		return 0;
	}
	
	fStart  = atof( argv[1] );
	fEnd 	= atof( argv[2] );
	dF 		= atof( argv[3] );
	
    if(argc == 6)
       delay = atoi( argv[5] );
    else
       delay = 1000;
	   
    fsweep(maxFreq, is160, is3200, allowPhase, noPTS, fStart, fEnd, dF, delay);
	
    return 0;
}
	
int fsweep(double maxFreq, int is160, int is3200, int allowPhase, int noPTS, double fstart, double fend, double dF, double delay)
{
	int i;
	int count;
	
	if(dF == 0.0 || fstart == fend)
	{
		set_pts(maxFreq, is160, is3200, allowPhase, noPTS, fstart, 0);
		return 0;
	}
	
	count = fabs( (fstart - fend) / dF );
	
	if(fstart > fend && dF > 0.0)  //Force proper increment sign.
		dF = -dF;
	else if(fstart < fend && dF < 0.0)
		dF = -dF;
	
	
	
	for(i=0; i <= count; ++i)
	{
		set_pts(maxFreq, is160, is3200, allowPhase, noPTS, fstart+i*dF, 0);
		Sleep( delay ); // delay in milliseconds
		//usleep( delay );  // For Linux
	}
	
	printf("%s\n", spinpts_get_error() );
	
	return 0;
}

void usage(char* argv[]) 
{
     printf("Invalid argument list. Usage:\n");
     printf("---------------------------------------------------------\n");
     printf("%s: [Start Frequency] [End Frequency] [Increment] [Phase] (Delay)\n",argv[0]);
     printf("Parameters in [] are required. Parameters in () are optional.\n");
     printf("Give Start Frequency, End Frequency and Increment in MHz.\n");
}
		
	
