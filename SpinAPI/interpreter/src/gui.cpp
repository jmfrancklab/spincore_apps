// PulseBlaster Interpreter GUI(version 2006-05-10)
// Written by Zachary Snow
//
// This file is the source code for the gui that runs over the top of the interpreter.

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

#include <windows.h>
#include <Shlobj.h> // for IsUserAnAdmin()
#include <stdio.h>
#include <direct.h>

#include <string>
#include <sstream>
using namespace std;

#define PB24
#include "spinapi.h"
#include "interpreter.h"
#include "resource.h"

HWND hWnd; // Window Handle

//
// Controls
//

HWND hEdit; // Edit Control
#define IDC_EDIT 1000
WNDPROC OldEditWndProc; 

HWND hOutput; // Output
#define IDC_OUTPUT 1001

HWND hOpen; // Load button
#define IDC_OPEN 1002

HWND hSave; // Save Button
#define IDC_SAVE 1003

HWND hProgram; // Program Button
#define IDC_PROGRAM 1004

HWND hStart; // Start button
#define IDC_START 1005

HWND hStop; // Stop button
#define IDC_STOP 1006

HWND hFrequencyLabel; // Frequency Label
#define IDC_FREQUENCYLABEL 1007

HWND hFrequency; // Frequency
#define IDC_FREQUENCY 1008

HWND hMhz; // MHZ Label
#define IDC_MHZ 1009

HWND hPos; // Position indicator
#define IDC_POS 1010

bool bChanged = false; // Has the open file changed?
bool bDebug = false; // Show debug info?

char ProgramPath[257]; // String to hold the path the program is installed in.
string OpenFileName; // Name of the currently open file.

//
// Menu Items
//

#define IDM_FILE_NEW    100
#define IDM_FILE_OPEN   101
#define IDM_FILE_SAVE   102
#define IDM_FILE_SAVEAS 103 
#define IDM_FILE_EXIT   104

#define IDM_INTERPRETER_DEBUG 110
#define IDM_INTERPRETER_SAVE  111
#define IDM_INTERPRETER_CLEAR 112

#define IDM_BOARD_PROGRAM 120
#define IDM_BOARD_START   121
#define IDM_BOARD_STOP    122

#define IDM_HELP_README 130
#define IDM_HELP_ABOUT  131

int Open();
int Save();
int SaveAs();
int Program();
int SaveOutput();

// Displays text in output box.
void Output(string output)
{
    SetWindowText(hOutput, output.c_str());
}

// Called when the window has been resized. Resizes controls.
void Resize()
{
	RECT clientRect;
    GetClientRect(hWnd, &clientRect);
	
	SetWindowPos(hOpen, NULL, clientRect.left, clientRect.top, 100, 30, SWP_NOZORDER);
	SetWindowPos(hSave, NULL, clientRect.left+100, clientRect.top, 100, 30, SWP_NOZORDER);
	SetWindowPos(hProgram, NULL, clientRect.left+200, clientRect.top, 100, 30, SWP_NOZORDER);
	SetWindowPos(hStart, NULL, clientRect.left+300, clientRect.top, 100, 30, SWP_NOZORDER);
	SetWindowPos(hStop, NULL, clientRect.left+400, clientRect.top, 100, 30, SWP_NOZORDER);
	
	SetWindowPos(hEdit, NULL, clientRect.left, 
	                          clientRect.top+30, 
							  clientRect.right - clientRect.left, 
	                          (clientRect.bottom - clientRect.top - 30 - 20) * .7, SWP_NOZORDER);
																  
	SetWindowPos(hOutput, NULL, clientRect.left, 
	                            (clientRect.bottom - clientRect.top - 30 - 20) * .7 + 30, 
								clientRect.right - clientRect.left, 
	                            (clientRect.bottom - clientRect.top - 30 - 20) * .3, SWP_NOZORDER);
								
	SetWindowPos(hFrequencyLabel, NULL, clientRect.left, 
	                                    (clientRect.bottom - clientRect.top - 30) + 10,
										150,
										20, SWP_NOZORDER);
										
	SetWindowPos(hFrequency, NULL, clientRect.left+150, 
	                               (clientRect.bottom - clientRect.top - 30) + 10,
							  	   150,
								   20, SWP_NOZORDER);

	SetWindowPos(hMhz, NULL, clientRect.left+310, 
	                         (clientRect.bottom - clientRect.top - 30) + 10,
							 50,
						     20, SWP_NOZORDER);
							 
	SetWindowPos(hPos, NULL, clientRect.left+360, 
	                         (clientRect.bottom - clientRect.top - 30) + 10,
							 (clientRect.right - clientRect.left - 360) ,
						     20, SWP_NOZORDER);
}

// Save Changes to open file
int SaveChanges()
{
	if(!bChanged) // If no changes made, just return success.
		return 1;
	
	int ret;
	// Ask to save changes.
	ret = MessageBox(hWnd, "Do you want to save the changes made to this file?", "Question", MB_YESNOCANCEL | MB_ICONQUESTION);
	
	if(ret == IDCANCEL)
	{
		// Return failure on cancel.
		return 0;
	}
	else if(ret == IDYES)
	{
		// If save succeeds, return success, otherwise failure.
		if(Save())
		{
			bChanged = false;
			return 1;
		}			
		else
			return 0;
	}
	else if(ret == IDNO)
	{
		// Don't save changes and return success.
		bChanged = false;
		return 1;
	}
	
	// Return failure, should never get to this point.
	return 0;
}

// Exit the program
void Exit()
{
	// If SaveChanges fails, don't exit.
	if(SaveChanges())
	{
		// Write config file on exit.
		
		FILE* pFile;
		FILE** ppFile = &pFile;
		
		_chdir(ProgramPath);
		fopen_s(ppFile, ".\\interpreter.cfg", "w");
		if(pFile)
		{
			char buffer[256];
			
			GetWindowText(hFrequency, buffer, 256);
			
			for(unsigned int i=0;i<256;i++)
				if(buffer[i] == '\r')
					buffer[i] = 0;
			
			fputs(buffer, pFile);
			
			if(bDebug)
				fprintf(pFile, "\ntrue");
			else
				fprintf(pFile, "\nfalse");
			
			fclose(pFile);
		}
		
		PostQuitMessage(0);
	}
}

// Sets the name of the window to display the name of the open file.
void SetName()
{
	if(OpenFileName != "")
	{
		unsigned int j;
		for(unsigned int i=0;i<OpenFileName.size();i++)
			if(OpenFileName[i] == '\\')
				j = i;				
	
		string name = OpenFileName.substr(j+1) + " - SpinCore PulseBlaster Interpreter";
		SetWindowText(hWnd, name.c_str());
	}
	else
	{
		SetWindowText(hWnd, "SpinCore PulseBlaster Interpreter");
	}
}

void ShowReadMe()
{
	string path = ProgramPath;
	path += "\\Doc\\index.html";
	ShellExecute(NULL, "open", path.c_str(), NULL, NULL, SW_SHOW);
}

// Window Proc
LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam)
{
	FILE* pFile;
    FILE** ppFile = &pFile;

    switch(msg)
    {
        case WM_DESTROY:
			DestroyWindow(hwnd);
		break;
		case WM_CLOSE:
			Exit();
        break;
		case WM_SIZE:
			Resize();
		break;
        case WM_COMMAND:
            // If something is typed in edit box, the file has been changed.
			if(HIWORD(wParam) == EN_CHANGE && LOWORD(wParam) == IDC_EDIT)
				bChanged = true;
			
			switch(LOWORD(wParam))
            {
				case IDM_FILE_NEW:
					if(SaveChanges())
					{
						// If save changes succeeds, clear the edit and output box.
						SetWindowText(hEdit, "");
						Output("");
						OpenFileName = "";
						SetName();
					}					
				break;
			
				case IDM_FILE_OPEN:
				case IDC_OPEN:
                    Open();
					SetName();
                break;
                case IDM_FILE_SAVE:
				case IDC_SAVE:
                    Save();
                break;
                case IDM_BOARD_PROGRAM:
				case IDC_PROGRAM:
                    Program();
                break;
				case IDM_BOARD_START:
                case IDC_START:
                    // Init board
                    if(pb_init() != 0)
                    {
	                  Output("PulseBlaster board not found.");
					  return 0;
                    }

                    // Start execution
					pb_start();

                    pb_close(); // Release board
                break;
				case IDM_BOARD_STOP:
                case IDC_STOP:
                    // Init board
                    if(pb_init() != 0)
                    {
					  Output("PulseBlaster board not found.");
					  return 0;
                    }

					// Stop execution
                    pb_stop();

                    pb_close(); // Release board
                break;
				
				// Menu
				
				case IDM_FILE_EXIT:
					Exit();
				break;
				
				case IDM_FILE_SAVEAS:
					SaveAs();
					SetName();
				break;
				
				case IDM_HELP_README:
					ShowReadMe();
				break;
				
				case IDM_HELP_ABOUT:
					// Display About message
					MessageBox(hwnd, INTERPRETER_VERSION, "About", MB_ICONINFORMATION | MB_OK);
				break;
				
				case IDM_INTERPRETER_DEBUG:
					// Flip the bDebug flag and check or uncheck the menu item.
					bDebug = !bDebug;
					
					if(bDebug)
						CheckMenuItem(GetSubMenu(GetMenu(hwnd), 1), IDM_INTERPRETER_DEBUG, MF_BYCOMMAND | MF_CHECKED);
					else
						CheckMenuItem(GetSubMenu(GetMenu(hwnd), 1), IDM_INTERPRETER_DEBUG, MF_BYCOMMAND | MF_UNCHECKED);
				break;
				
				case IDM_INTERPRETER_SAVE:
					SaveOutput();
				break;
				
				case IDM_INTERPRETER_CLEAR:
					SetWindowText(hOutput, "");
				break;
            }
        // This means the message isn't anything we can use
		default:
            return DefWindowProc(hwnd, msg, wParam, lParam);
    }
    // We processed the message
	return 0;
}

// Subclass Proc for Edit box.
LRESULT CALLBACK EditWndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam)
{
	if(msg == WM_KEYUP || msg == WM_LBUTTONUP)
	{
		// Calculate the position of the cursor
		
		unsigned int pos = 0;
		SendMessage(hEdit, EM_GETSEL, (WPARAM)&pos, 0);
		
		char *buffer = new char[pos+1];
		GetWindowText(hEdit, buffer, pos+1);
		
		unsigned int line=1, col=1;
		for(unsigned int i=0;i<pos+1;i++)
		{
			if(buffer[i] == '\r')
				continue;
		
			if(buffer[i] == '\n')
			{
				line++;
				col = 0;
			}
			
			col++;
		}
		
		delete buffer;
		
		// Display position on Position Control
		char buffer2[256];
		sprintf_s(buffer2, "Line %d, Column %d", line, col-1);
		SetWindowText(hPos, buffer2);
	}
	
	// Pass message on to default edit proc.
	return CallWindowProc(OldEditWndProc, hwnd, msg, wParam, lParam);
}

// Main function.
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance,
    LPSTR lpCmdLine, int nCmdShow)
{
    //
    // Begin Window creation code
    //

	// Register class.
	
    WNDCLASSEX wc;
    MSG Msg;

    wc.cbSize        = sizeof(WNDCLASSEX);
    wc.style         = 0;
    wc.lpfnWndProc   = WndProc;
    wc.cbClsExtra    = 0;
    wc.cbWndExtra    = 0;
    wc.hInstance     = hInstance;
    wc.hIcon         = LoadIcon(hInstance, MAKEINTRESOURCE(IDI_ICON1));
    wc.hCursor       = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW);
    wc.lpszMenuName  = NULL;
    wc.lpszClassName = "MyWindowClass";
    wc.hIconSm       = LoadIcon(hInstance, MAKEINTRESOURCE(IDI_ICON1));

    if(!RegisterClassEx(&wc))
    {
        MessageBox(NULL, "Window Registration Failed!", "Error!",
            MB_ICONEXCLAMATION | MB_OK);
        return 0;
    }

	//if(!IsUserAnAdmin()) {
	//	MessageBox(NULL,"Please run as administrator.",NULL,MB_OK);
	//	return 0;
	//}

	// Build Menu.
	
	HMENU hFileMenu = CreateMenu();
	AppendMenu(hFileMenu, MF_STRING, IDM_FILE_NEW, "&New");
	AppendMenu(hFileMenu, MF_STRING, IDM_FILE_OPEN, "&Open...");
	AppendMenu(hFileMenu, MF_STRING, IDM_FILE_SAVE, "&Save");
	AppendMenu(hFileMenu, MF_STRING, IDM_FILE_SAVEAS, "Save &As...");
	AppendMenu(hFileMenu, MF_STRING, IDM_FILE_EXIT, "E&xit");
	
	HMENU hInterpreterMenu = CreateMenu();
	AppendMenu(hInterpreterMenu, MF_STRING, IDM_INTERPRETER_DEBUG, "Show &Debug Information");
	AppendMenu(hInterpreterMenu, MF_STRING, IDM_INTERPRETER_SAVE, "&Save Output...");
	AppendMenu(hInterpreterMenu, MF_STRING, IDM_INTERPRETER_CLEAR, "&Clear Output");
	
	HMENU hBoardMenu = CreateMenu();
	AppendMenu(hBoardMenu, MF_STRING, IDM_BOARD_PROGRAM, "&Load");
	AppendMenu(hBoardMenu, MF_STRING, IDM_BOARD_START, "&Start");
	AppendMenu(hBoardMenu, MF_STRING, IDM_BOARD_STOP, "S&top");
	
	HMENU hHelpMenu = CreateMenu();
	AppendMenu(hHelpMenu, MF_STRING, IDM_HELP_README, TEXT("&Read Me..."));
	AppendMenu(hHelpMenu, MF_STRING, IDM_HELP_ABOUT, "&About...");
	
	HMENU hMenu = CreateMenu();
	AppendMenu(hMenu, MF_STRING | MF_POPUP, (unsigned int)hFileMenu, "&File");
	AppendMenu(hMenu, MF_STRING | MF_POPUP, (unsigned int)hInterpreterMenu, "&Interpreter");
	AppendMenu(hMenu, MF_STRING | MF_POPUP, (unsigned int)hBoardMenu, "&Board");
	AppendMenu(hMenu, MF_STRING | MF_POPUP, (unsigned int)hHelpMenu, "&Help");
	
	// Create window and controls.
	
    hWnd = CreateWindowEx(
        WS_EX_CLIENTEDGE,
        "MyWindowClass",
        "SpinCore PulseBlaster Interpreter",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, 640, 480,
        NULL, hMenu, hInstance, NULL);

    if(hWnd == NULL)
    {
        MessageBox(NULL, "Window Creation Failed!", "Error!",
            MB_ICONEXCLAMATION | MB_OK);
        return 0;
    }

    hEdit = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "",
            WS_CHILD | WS_VISIBLE | ES_MULTILINE | WS_VSCROLL | WS_HSCROLL | ES_AUTOVSCROLL | ES_AUTOHSCROLL,
            0, 0, 1, 1, hWnd, (HMENU)IDC_EDIT, GetModuleHandle(NULL), NULL);

    if(hEdit == NULL)
        MessageBox(hWnd, "Could not create Edit box.", "Error", MB_OK | MB_ICONERROR);
		
	OldEditWndProc = (WNDPROC)SetWindowLongPtr(hEdit, GWLP_WNDPROC, (LONG_PTR)EditWndProc);

	HFONT hFont = CreateFont(12, 12, 0, 0, 
		FW_DONTCARE, 0, 0, 0, 
		ANSI_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, 
		FF_DONTCARE, "Courier");
	
	if(hFont)
		SendMessage(hEdit, WM_SETFONT, (WPARAM)hFont, (LPARAM)TRUE);

   hOutput = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "",
            WS_CHILD | WS_VISIBLE | ES_MULTILINE | WS_VSCROLL | WS_HSCROLL | ES_AUTOVSCROLL | ES_AUTOHSCROLL | ES_READONLY,
            0, 0, 1, 1, hWnd, (HMENU)IDC_EDIT, GetModuleHandle(NULL), NULL);
    if(hOutput == NULL)
        MessageBox(hWnd, "Could not create Output box.", "Error", MB_OK | MB_ICONERROR);

	HFONT hFont2 = CreateFont(12, 12, 0, 0, FW_BOLD, 0, 0, 0, ANSI_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, FF_DONTCARE, "Courier");
		
	if(hFont2)
		SendMessage(hOutput, WM_SETFONT, (WPARAM)hFont2, (LPARAM)TRUE);
		
    hOpen = CreateWindowEx(0, "BUTTON", "Open File",
            WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON | BS_MULTILINE | BS_CENTER,
            0, 0, 1, 1, hWnd, (HMENU)IDC_OPEN, GetModuleHandle(NULL), NULL);
    if(hOpen == NULL)
        MessageBox(hWnd, "Could not create Load button.", "Error", MB_OK | MB_ICONERROR);

    hSave = CreateWindowEx(0, "BUTTON", "Save File",
            WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON | BS_MULTILINE | BS_CENTER,
            0, 0, 1, 1, hWnd, (HMENU)IDC_SAVE, GetModuleHandle(NULL), NULL);
    if(hSave == NULL)
        MessageBox(hWnd, "Could not create Save button.", "Error", MB_OK | MB_ICONERROR);

    hProgram = CreateWindowEx(0, "BUTTON", "Load Board",
               WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON | BS_MULTILINE | BS_CENTER,
               0, 0, 1, 1, hWnd, (HMENU)IDC_PROGRAM, GetModuleHandle(NULL), NULL);
    if(hProgram == NULL)
        MessageBox(hWnd, "Could not create Save button.", "Error", MB_OK | MB_ICONERROR);

    hStart = CreateWindowEx(0, "BUTTON", "Start",
             WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON | BS_MULTILINE | BS_CENTER,
             0, 0, 1, 1, hWnd, (HMENU)IDC_START, GetModuleHandle(NULL), NULL);
    if(hStart == NULL)
        MessageBox(hWnd, "Could not create Start button.", "Error", MB_OK | MB_ICONERROR);

    hStop = CreateWindowEx(0, "BUTTON", "Stop",
            WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON | BS_MULTILINE | BS_CENTER,
            0, 0, 1, 1, hWnd, (HMENU)IDC_STOP, GetModuleHandle(NULL), NULL);
    if(hStop == NULL)
        MessageBox(hWnd, "Could not create Start button.", "Error", MB_OK | MB_ICONERROR);
			
	hFrequencyLabel = CreateWindowEx(0, "STATIC", "Clock Frequency:",
                      WS_CHILD | WS_VISIBLE | SS_CENTER,
                      0, 0, 1, 1, hWnd, (HMENU)IDC_FREQUENCYLABEL, GetModuleHandle(NULL), NULL);
    if(hFrequencyLabel == NULL)
        MessageBox(hWnd, "Could not create frequency label.", "Error", MB_OK | MB_ICONERROR);
			
	hFrequency = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "",
                 WS_CHILD | WS_VISIBLE,
                 0, 0, 1, 1, hWnd, (HMENU)IDC_FREQUENCY, GetModuleHandle(NULL), NULL);
    if(hEdit == NULL)
        MessageBox(hWnd, "Could not create Frequency box.", "Error", MB_OK | MB_ICONERROR);
			
	hMhz = CreateWindowEx(0, "STATIC", "MHz",
           WS_CHILD | WS_VISIBLE | SS_LEFT,
           0, 0, 1, 1, hWnd, (HMENU)IDC_MHZ, GetModuleHandle(NULL), NULL);
    if(hMhz == NULL)
		MessageBox(hWnd, "Could not create frequency label.", "Error", MB_OK | MB_ICONERROR);

	hPos = CreateWindowEx(0, "STATIC", "Line 1, Column 1",
           WS_CHILD | WS_VISIBLE | SS_CENTER,
           0, 0, 1, 1, hWnd, (HMENU)IDC_POS, GetModuleHandle(NULL), NULL);
    if(hPos == NULL)
		MessageBox(hWnd, "Could not create position label.", "Error", MB_OK | MB_ICONERROR);
		
	Resize();
			
    ShowWindow(hWnd, nCmdShow);
		UpdateWindow(hWnd);
    //
    // End Window creation code
    //
	
	// Open registry and find where program is installed.
	
	HKEY hKey;
	if(RegOpenKeyEx(HKEY_LOCAL_MACHINE, "SOFTWARE\\SpinCore\\PulseBlaster Interpreter\\", 0, KEY_READ, &hKey) == ERROR_SUCCESS)
	{
		unsigned int RegValueSize = 256;
		RegQueryValueEx(hKey, NULL, NULL, NULL, (LPBYTE)(&ProgramPath), (ULONG*)&RegValueSize);
		ProgramPath[256] = 0;
		RegCloseKey(hKey);
	}
	else
	{
		ProgramPath[0] = 0;
	}
	
	// Check for a command line parameter
	FILE* pFile = NULL;
	FILE** ppFile = &pFile;
	if(strcmp(lpCmdLine, "") != 0)
	{
		char buffer[257];
		
		// Get rid of " "
		unsigned int j=0;
		for(unsigned int i=0;lpCmdLine[i] != 0 && i<256;i++)
			if(lpCmdLine[i] != '\"')
				buffer[j++] = lpCmdLine[i];
				
		buffer[j] = 0;
	
		// Convert file name to LongPathName
		GetLongPathName(buffer, buffer, 256);
		buffer[256] = 0;
		
		// Read in file
		fopen_s(ppFile, buffer, "r");
		
		if(pFile)
		{
			std::string str;

		    char ch;
		    while(!feof(pFile))
		    {
		        ch = (char)fgetc(pFile);

		        if(ch == EOF)
		            break;

		        if(ch != '\n')
		            str += ch;
		        else
		        {
		            str += '\r';
		            str += '\n';
		        }
		    }

		    fclose(pFile);

		    SetWindowText(hEdit, str.c_str());

		    Output("File opened.");
			
			OpenFileName = buffer;
		}
		else
		{
			char buffer2[1025];
			sprintf_s(buffer2, "Unable to open %s.", buffer);
			buffer2[1024] = 0;
			MessageBox(hWnd, buffer2, "Error", MB_ICONERROR | MB_OK);
			OpenFileName = "";
		}
	}
	else
	{
		OpenFileName = "";
	}
	
	// Set name of Window
	SetName();
	
	// Open config file.
	
	_chdir(ProgramPath);
	fopen_s(ppFile, ".\\interpreter.cfg", "r");
	if(!pFile)
	{
		SetWindowText(hFrequency, "100.0");
	}
	else
	{
		char line[256];
		
		fgets(line, 256, pFile);
		
		for(unsigned int i=0;i<256;i++)
			if(line[i] == '\n')
				line[i] = 0;
		
		SetWindowText(hFrequency, line);
		
		fgets(line, 256, pFile);
		if(!strncmp(line, "true", 4))
			bDebug = true;
		
		if(bDebug)
			CheckMenuItem(GetSubMenu(GetMenu(hWnd), 1), IDM_INTERPRETER_DEBUG, MF_BYCOMMAND | MF_CHECKED);
	
		fclose(pFile);
	}
		
    // Check for board.
	if(pb_init() != 0)
    {
		Output("No PulseBlaster board found.");
    }
	else
	{
		// If found display SpinAPI version
		string output = "PulseBlaster board found.\r\nUsing SpinAPI version ";
		output += pb_get_version();
		output += '.';
		Output(output);
		pb_set_debug(1);
		pb_close();  // Release board
	}	
	
    // Message Pump
    while(GetMessage(&Msg, NULL, 0, 0) > 0)
    {
        TranslateMessage(&Msg);
        DispatchMessage(&Msg);
    }

    // Init board
    if(pb_init() == 0)
    {
		pb_stop(); // Stop execution of program
		pb_close(); // Release board
	}
	
    return Msg.wParam;
}

// Open a file.
int Open()
{
	// If SaveChanges fails, don't try to open another file and return failure.
	if(!SaveChanges())
		return 0;
    
	//Display open file dialog.
	OPENFILENAME ofn;
    char filename[257] = "";

    ZeroMemory(&ofn, sizeof(ofn));

    ofn.lStructSize = sizeof(ofn);
    ofn.hwndOwner = hWnd;
    ofn.lpstrFilter = "PulseBlaster Files (*.pb)\0*.pb\0All Files (*.*)\0*.*\0";
    ofn.lpstrFile = filename;
    ofn.lpstrInitialDir = ".";
    ofn.nMaxFile = MAX_PATH;
    ofn.Flags = OFN_EXPLORER | OFN_FILEMUSTEXIST | OFN_HIDEREADONLY;
    ofn.lpstrDefExt = "pb";

    if(!GetOpenFileName(&ofn))
    {
        // Cancel button was chosen.
		Output("No file opened.");
        return 0;
    }

	FILE* pFile;
    FILE** ppFile = &pFile;
	fopen_s(ppFile, filename, "r");
    if (pFile==0)
    {
        string error = "Error opening ";
		error += filename;
		error += '.';
		Output(error);
        return 0;
    }

    std::string str;

	// Convert \n's to \r\n's
    char ch;
    while(!feof(pFile))
    {
        ch = (char)fgetc(pFile);

        if(ch == EOF)
            break;

        if(ch != '\n')
            str += ch;
        else
        {
            str += '\r';
            str += '\n';
        }
    }

    fclose(pFile);

    // Set edit box text.
	SetWindowText(hEdit, str.c_str());

    OpenFileName = filename;
	
	// Display file was opened.
	string output = "Opened ";
	output += filename;
	output += ".";
	Output(output);
	
    return 1;
}

// Save file.
int Save()
{
	// If we don't know where to save to call SaveAs instead.
	if(OpenFileName == "")
		return SaveAs();
	
	int length = GetWindowTextLength(hEdit);
    char *data = new char[length+1];
    GetWindowText(hEdit, data, length+1);
    data[length] = 0;

    FILE* pFile;
    FILE** ppFile = &pFile;
	fopen_s(ppFile, OpenFileName.c_str(), "w");
    if (pFile==0)
    {
        string error = "Error opening ";
		error += OpenFileName;
		error += '.';
		Output(error);
        return 0;
    }

	// Write everything to file except for \r
    for(int i=0;i<length;i++)
		if(data[i] != '\r')
			fputc(data[i], pFile);

    fclose(pFile);

    delete data;

	// File is current
	bChanged = false;
	
	// Display file saved message.
	string output = "Wrote ";
	output += OpenFileName;
	output += ".";
	Output(output);
	
    return 1;
}

// Save As.
int SaveAs()
{
    // Display save file dialog.
	OPENFILENAME ofn;
    char filename[257] = "";

    ZeroMemory(&ofn, sizeof(ofn));

    ofn.lStructSize = sizeof(ofn);
    ofn.hwndOwner = hWnd;
    ofn.lpstrFilter = "PulseBlaster Files (*.pb)\0*.pb\0All Files (*.*)\0*.*\0";
    ofn.lpstrFile = filename;
    ofn.lpstrInitialDir = ".";
    ofn.nMaxFile = MAX_PATH;
    ofn.Flags = OFN_EXPLORER | OFN_HIDEREADONLY | OFN_OVERWRITEPROMPT;
    ofn.lpstrDefExt = "pb";

    if(!GetSaveFileName(&ofn))
    {
		// Cancel button chosen.
        Output("File not saved.");
        return 0;
    }

    int length = GetWindowTextLength(hEdit);
    char *data = new char[length+1];
    GetWindowText(hEdit, data, length+1);
    data[length] = 0;

    FILE* pFile;
    FILE** ppFile = &pFile;
	fopen_s(ppFile, filename, "w");
    if (pFile==0)
    {
        string error = "Error opening ";
		error += filename;
		error += '.';
		Output(error);
        return 0;
    }

    // Write everything to file except for \r
	for(int i=0;i<length;i++)
		if(data[i] != '\r')
			fputc(data[i], pFile);

    fclose(pFile);

    delete data;

	// File is current.
	bChanged = false;
	
	OpenFileName = filename;
	
	// Display file saved message.
	string output = "Wrote ";
	output += filename;
	output += ".";
	Output(output);
	
    return 1;
}

// Program the board.
int Program()
{
	int i;
	char filename[256];
    tmpnam_s(filename, 256);

	// Write edit box contents to a temporary file.
    int datalength = GetWindowTextLength(hEdit);
    char *data = new char[datalength+1];
    GetWindowText(hEdit, data, datalength+1);
    data[datalength] = 0;
	
    FILE* pFile;
    FILE** ppFile = &pFile;
	fopen_s(ppFile, filename, "w");
    if (pFile==0)
    {
        string error = "Error opening ";
		error += filename;
		error += '.';
        return 0;
    }

	// Don't write \r
    for(i=0;i<datalength;i++)
		if(data[i] != '\r')
			fputc(data[i], pFile);

    fclose(pFile);

    delete data;

	// Get frequency
	char buffer[256];
	GetWindowText(hFrequency, buffer, 256);
	double frequency = atof(buffer);

	ostringstream outputStream;
	
	// Call interpreter.
	if(!Interpret(frequency, filename, outputStream, bDebug))
		MessageBox(hWnd, "Failed to program board.", "Error", MB_ICONERROR | MB_OK);
	string output = outputStream.str();
	string output2;
	
	// Convert interpreter output.
	for(i=0;i<((int)output.size());i++)
	{
		if(output[i] == '\n')
			output2 += "\r\n";
		else
			output2 += output[i];
	}
	
	// Display interpreter output.
	Output(output2);
	
	remove(filename);
	
	return 1;
}

// Save output box.
int SaveOutput()
{
	// Display save file dialog.
	OPENFILENAME ofn;
    char filename[257] = "";

    ZeroMemory(&ofn, sizeof(ofn));

    ofn.lStructSize = sizeof(ofn);
    ofn.hwndOwner = hWnd;
    ofn.lpstrFilter = "Text Files (*.txt)\0*.txt\0All Files (*.*)\0*.*\0";
    ofn.lpstrFile = filename;
    ofn.lpstrInitialDir = ".";
    ofn.nMaxFile = MAX_PATH;
    ofn.Flags = OFN_EXPLORER | OFN_HIDEREADONLY | OFN_OVERWRITEPROMPT;
    ofn.lpstrDefExt = "txt";

    if(!GetSaveFileName(&ofn))
    {
        Output("File not saved.");
        return 0;
    }

	// Write file.
    int length = GetWindowTextLength(hOutput);
    char *data = new char[length+1];
    GetWindowText(hOutput, data, length+1);
    data[length] = 0;

    FILE* pFile;
    FILE** ppFile = &pFile;
	fopen_s(ppFile, filename, "w");
    if (pFile==0)
    {
        string error = "Error opening ";
		error += filename;
		error += '.';
		Output(error);
        return 0;
    }

    for(int i=0;i<length;i++)
		if(data[i] != '\r')
			fputc(data[i], pFile);

    fclose(pFile);

    delete data;

	// Display message saying file was written.
	string output = "Wrote ";
	output += filename;
	output += ".";
	Output(output);
	
    return 1;
}
