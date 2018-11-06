// PulseBlaster Interpreter Command Line(version 2006-05-10)
// Written by Zachary Snow
//
// This file is the source code for the command line that passes parameters to the interpreter.

/* Copyright (c) 2006 SpinCore Technologies, Inc.
 *
 * This software is provided 'as-is', without any expressed or implied warranty.
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

#include <string.h>

#include <iostream>
#include <cstdlib>
using namespace std;

#define PB24
#include <spinapi.h>
#include "interpreter.h"

void DisplayUsage()
{
	cout<<"Usage: spbicl <command> [file] [frequency]"<<endl;
	cout<<"Commands:"<<endl;
	cout<<"  Load = Load [file] into memory using [frequency]"<<endl;
	cout<<"  Start = Start execution of program currently in memory"<<endl;
	cout<<"  Stop = Stop execution of program currently running"<<endl;
}

int main(int argc, char *argv[])
{
	unsigned int i;

	if(argc < 2)
	{
		DisplayUsage();
		return 0;
	}

	char command[6];
	for(i=0;i<5 && argv[1][i] != 0;i++)
		command[i] = (char)toupper(argv[1][i]);
	command[i] = 0;
	
	if(strcmp(command, "LOAD") == 0)
	{
		if(argc < 4)
		{
			cout<<"Please specify the file to load and the frequency to use."<<endl<<endl;
			DisplayUsage();
		}
		else
		{
			double frequency = atof(argv[3]);
			if(Interpret(frequency, argv[2], cout, true) == 0)
				return -1;
		}
	}
	else if(strcmp(command, "START") == 0)
	{
		// Init board
		if(pb_init() != 0)
		{
			cout<<"PulseBlaster board not found."<<endl;
			return -1;
		}

		// Start execution
		pb_start();

		pb_close(); // Release board
		
		cout<<"Program execution started."<<endl;
	}
	else if(strcmp(command, "STOP") == 0)
	{
		// Init board
		if(pb_init() != 0)
		{
			cout<<"PulseBlaster board not found."<<endl;
			return -1;
		}

		// Stop execution
		pb_stop();

		pb_close(); // Release board
		
		cout<<"Program execution stopped."<<endl;
	}
	else
	{
		cout<<"Unknown Command."<<endl<<endl;
		DisplayUsage();
	}
	
	return 0;
}