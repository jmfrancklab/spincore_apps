PulseBlaster Interpreter Readme
Build 20081118

Sections
1: Legal
2: Language
3: User Interface

----------------
Section 1: Legal
----------------

	Copyright (c) 2007 SpinCore Technologies, Inc.
  
	This software is provided 'as-is', without any express or implied warranty.
	In no event will the authors be held liable for any damages arising from the
	use of this software.
  
	Permission is granted to anyone to use this software for any purpose,
	including commercial applications, and to alter it and redistribute it
	freely, subject to the following restrictions:
 
	1. The origin of this software must not be misrepresented; you must not
	   claim that you wrote the original software. If you use this software in a
	   product, an acknowledgment in the product documentation would be appreciated
	   but is not required.
	2. Altered source versions must be plainly marked as such, and must not be
	   misrepresented as being the original software.
	3. This notice may not be removed or altered from any source distribution.

-------------------
Section 2: Language
-------------------

	The language of the interpreter is very similar in appearance to that of an assembly language.
Every line represents a single instruction. White space such as tabs and spaces are thrown away.
The language is case-insensative. The following are instructions on the contents of a given line.


Labels
------

	Labels come at the beginning of a line and are denoted by a : at the end. For instance:
	
Start: 0xFFFFFF, 200 ms

	This line is labeled Start. Since the language is case insensative though, the label is equal to
any form of the Start. Lables are optional and do not have to be contained on every line.

Output Pattern
--------------

	This is the first required part for a given line. This field must exist on all lines or the interpreter
will fail while programming the board. This field represents the pattern that the board will output for this
instruction. This pattern may be represented in Hex, Binary, or simply Integer format. All output fields must
begin with a number no matter what format they are represented int. This usually only matters for Hex and Binary
representations. Hex and Binary representations should start with a 0 followed by an 'x' or a 'b'. The following
are examples of valid output patterns for all bits on:

Hex:     0xFFFFFF
Binary:  0b1111 1111 1111 1111 1111 1111
Integer: 16777215

	Notice how Hex and Binary begin with "0x" and "0b". The x or the b must be there otherwise the interpreter
will fail while trying to program the board. Also notice that the binary output pattern contains white space.
This is allowed. You may also do:

0x FF FF FF

	The output pattern is read until a comma is reached. All white space is thrown away during the read.
	
Time Field
----------

	The time field consists of two parts, time value and time units. Time value can be any decimal number.
Time units must be one of four options:

s for seconds
ms for milliseconds
us for microseconds
ns for nanoseconds

	Examples of valid time fields are as follows:
	
500 ms
500ms
500.0 ms
500.0ms

	White space is permitted. 
	
Command Field
-------------

	The command field tells the board what to do after the producing the output pattern for the given
amount of time. Valid commands are as follows:

CONTINUE or continue
STOP or stop
LOOP or loop
END_LOOP or end_loop
JSR or jsr
RTS or rts
BRANCH or branch
LONG_DELAY or long_delay
WAIT or wait

	The command field is optional. If no command field is listed, the CONTINUE command will be assumed.
For more information on these commands see the spinapi reference. 
(http://www.pulseblaster.com/CD/spinapi/spinapi_reference/spinapi_8h.html#a63)

Data Field
----------

	The data field is also optional unless a branch, end_loop, or jsr command is used during an instruction. 
In this case, the interpreter forces you to enter a label to jump to. The data field is used for different 
purposes depending on the command field. If no data field is specified, a value of 0 will be assumed.
For more information see the spinapi reference.
(http://www.pulseblaster.com/CD/spinapi/spinapi_reference/spinapi_8h.html#a63)

Comments
--------

	Comments start with a // and the interpreter just throws them out. A comment runs to the end of a given 
line. They can be on a line my themselves or placed after an instruction as follows:

// Valid comment on a line by itself.
Label: 0xFFFFFF, 100 ms // Valid comment after a valid instruction
       0x000000, 100 ms, branch, Label // Another valid comment


	There are several example programs available. Please take a look at these.
	   
-------------------------
Section 3: User Interface
-------------------------

	Upon launching the program, you will be presented with a GUI interface for writing your PulseBlaster
programs. The top white box is an editor. The bottom gray box is output that the interpreter produces. 
At the bottom of the window is a box to put in the frequency your board uses. This frequency will be saved 
each time you shutdown the program and then reloaded the next time you launch. On the bottom right, you will
notice Line # and Column # output. This tells you where the cursor is inside of the white box for fixing 
errors and such.

	At the top of the window is the menu bar and 5 buttons. The buttons perform many of the same functions
that can be found on the menu bar but are provided as a convenience. Starting from left to right:

Open File
	This button opens a file. You will be prompted to save any changes to the contents of the current file.
	
Save File
	This button saves the file you are currently editing.
	
Load Board
	This button loads the program that currently resides in the white box onto the board. The file does not
have to be saved beforehand. The program will take the contents of the white box and interpret them. The output
of this operation will be displayed in the gray box. Upon success, a message will be displayed saying the board
was successfully loaded. If this message is not displayed, it means that some error occured and a message telling
you the error should be the last thing displayed.

Start
	This button starts execution of the program currently in the board's memory.
	
Stop
	This button stops execution of the program current in the board's memory.
	
	The menu bar is just above the 5 buttons. Starting from left to right:
	
File->New
	This will erase the current contents of the white box. You will be prompted to save changes to the 
current file.
	
File->Open
	Same as the Open File button.
	
File->Save
	Same as the Save File button.
	
File->Exit
	This will exit the program. You will be prompted to save changes to the current file.
	
Interpreter->Show Debug Information
	This turns debug information from the interpreter on and off. This might provide some insight into
an error that you might not be able to resolve. The debug information will be shown next time the board is
loaded.

Interpreter->Save Output
	This saves the contents of the gray box to a text file.
	
Interpreter->Clear Output
	This clears the contents of the gray box.
	
Board->Load
	Same as Load Board button.

Board->Start
	Same as Start button.
	
Board->Stop
	Same as Stop button.
	
Help->About
	This displays information about the program.





