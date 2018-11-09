// PulseBlaster Interpreter (version 2006-05-10)
// Written by Zachary Snow
//
// PulseBlaster Interpreter.

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

#include <vector>
#include <stack>
#include <string>
#include <iostream>
#include <sstream>
#include <cstdio>
#include <cstdlib>
#include <cstring>

#define PB24
#include <spinapi.h>

typedef struct tagToken
{
	enum TokenType { Identifier = 0, Numeric, Variable, Colon, Comma, Equal, EndOfLine, EndOfFile };
	TokenType type;
	std::string value;
	unsigned int lineNum, colNum;
} Token;

typedef struct tagProgramLine
{
	std::string output;
	std::string time;
	std::string timeunit;
	std::string command;
	std::string data;
	unsigned int lineNum;
} ProgramLine;

typedef struct tagLabel
{
	std::string name;
	int line;
} Label;

typedef struct tagVariable
{
	std::string name;
	std::string value;
	unsigned int lineNum;
} Variable;

int BinaryStringToInteger(const char *input, int *output)
{
	unsigned int i = 0;

	(*output) = 0;

	while(input[i] != 0)
	{
		if(input[i] != '1' && input[i] != '0')
			return 0;

		if(input[i] == '1')
			(*output) += 1;
		
		if(input[i+1] != 0)
			(*output)<<=1;

		i++;
	}

	return 1;
}

int HexStringToInteger(const char *input, int *output)
{
	unsigned int i = 0;
	
	(*output) = 0;
	
	while(input[i+1] != 0)
		i++;
		
	unsigned int value;
	unsigned int multiplier = 1;
	
	while(true)
	{
		switch(input[i])
		{
			case '0': value = 0; break;
			case '1': value = 1; break;
			case '2': value = 2; break;
			case '3': value = 3; break;
			case '4': value = 4; break;
			case '5': value = 5; break;
			case '6': value = 6; break;
			case '7': value = 7; break;
			case '8': value = 8; break;
			case '9': value = 9; break;
			case 'A': value = 10; break;
			case 'B': value = 11; break;
			case 'C': value = 12; break;
			case 'D': value = 13; break;
			case 'E': value = 14; break;
			case 'F': value = 15; break;
			default:
				return 0;
		}
	
		(*output) += value * multiplier;
		
		if(i == 0)
			break;
		
		i--;
		multiplier *= 16;
	}
	
	return 1;
}

int NaturalLanguage(const char *input, int *output)
{
	unsigned int i = 0;
	
	(*output) = 0;
	
	std::string number = "";
	
	while(true)
	{
		if(input[i] != '+' && input[i] != 0)
		{
			number += input[i];
		}
		else
		{
			if(number == "0")
				(*output) |= 1;
			else if(number == "1")
				(*output) |= 2;
			else if(number == "2")
				(*output) |= 4;
			else if(number == "3")
				(*output) |= 8;
			else if(number == "4")
				(*output) |= 16;
			else if(number == "5")
				(*output) |= 32;
			else if(number == "6")
				(*output) |= 64;
			else if(number == "7")
				(*output) |= 128;
			else if(number == "8")
				(*output) |= 256;
			else if(number == "9")
				(*output) |= 512;
			else if(number == "10")
				(*output) |= 1024;
			else if(number == "11")
				(*output) |= 2048;
			else if(number == "12")
				(*output) |= 4096;
			else if(number == "13")
				(*output) |= 8192;
			else if(number == "14")
				(*output) |= 16384;
			else if(number == "15")
				(*output) |= 32768;
			else if(number == "16")
				(*output) |= 65536;
			else if(number == "17")
				(*output) |= 131072;
			else if(number == "18")
				(*output) |= 262144;
			else if(number == "19")
				(*output) |= 524288;
			else if(number == "20")
				(*output) |= 1048576;
			else if(number == "21")
				(*output) |= 2097152;
			else if(number == "22")
				(*output) |= 4194304;
			else if(number == "23")
				(*output) |= 8388608;
			else
				return 0;
				
			number = "";
		}
		
		if(input[i] == 0)
			break;
		
		i++;
	}
	
	return 1;
}

int CommandLookup(const char *word)
{
	if(!strcmp(word, "CONTINUE"))
	{
		return CONTINUE;
	}
	else if(!strcmp(word, "STOP"))
	{
		return STOP;
	}
	else if(!strcmp(word, "LOOP"))
	{
		return LOOP;
	}
	else if(!strcmp(word, "END_LOOP"))
	{
		return END_LOOP;
	}
	else if(!strcmp(word, "JSR"))
	{
		return JSR;
	}
	else if(!strcmp(word, "RTS"))
	{
		return RTS;
	}
	else if(!strcmp(word, "BRANCH"))
	{
		return BRANCH;
	}
	else if(!strcmp(word, "LONG_DELAY"))
	{
		return LONG_DELAY;
	}
	else if(!strcmp(word, "WAIT"))
	{
		return WAIT;
	}
	
	return -1;
}

std::string Convert(std::string value)
{
	if(value == "\n")
		return "End of Line";
	else if(value == "EOF")
		return "End of File";
	else
		return value;
}

int Interpret(double frequency, char *filename, std::ostream& outputStream, bool bDebug = false)
{
	std::vector<Token> tokens;
	unsigned int i;
	
	//
	// Scan for Tokens
	//
	
	FILE* pFile;
	FILE** ppFile = &pFile;
	fopen_s(ppFile, filename, "r");
	if(!pFile)
	{
		outputStream<<"Failed to open file."<<std::endl;
		return 0;
	}
		
	Token token;
	char ch = ' ';

	bool bRead = true;
	bool bStuck = false;
	unsigned int lineNum = 1;
	unsigned int colNum = 0;
	
	while(!feof(pFile))
	{
		if(bStuck)
		{
			outputStream<<"Reading of tokens failed at Line "<<lineNum<<" Column "<<colNum<<'.'<<std::endl;
			outputStream<<"Offending character: \""<<ch<<"\"."<<std::endl;
			return 0;
		}
		
		if(bRead)
		{
			ch = (char)toupper(fgetc(pFile));
			colNum++;
			bStuck = true;
		}
	
		if(isalpha(ch))
		{
			token.type = Token::Identifier;
			
			token.lineNum = lineNum;
			token.colNum = colNum;
			
			token.value = "";
		
			while(ch != ',' && ch != ':' && ch != '=' && ch != '/' && ch != '\n' && ch != EOF)
			{
				if(ch != ' ')
					token.value += ch;
				
				ch = (char)toupper(fgetc(pFile));
				colNum++;
			}
			
			tokens.push_back(token);
			bRead = false;
			bStuck = true;
		}
		else if(isdigit(ch))
		{
			token.type = Token::Numeric;
			
			token.lineNum = lineNum;
			token.colNum = colNum;
			
			token.value = "";
		
			while(ch != ',' && ch != ':' && ch != '=' && ch != '/' && ch != '\n' && ch != EOF)
			{
				if(ch != ' ')
					token.value += ch;
				
				ch = (char)toupper(fgetc(pFile));
				colNum++;
			}
			
			tokens.push_back(token);
			bRead = false;
			bStuck = true;
		}
		else if(ch == '$')
		{
			token.type = Token::Variable;
			
			token.lineNum = lineNum;
			token.colNum = colNum;
			
			token.value = "";
			
			while(ch != ',' && ch != ':' && ch != '=' && ch != '/' && ch != '\n' && ch != EOF)
			{
				if(ch != ' ')
					token.value += ch;
				
				ch = (char)toupper(fgetc(pFile));
				colNum++;
			}
			
			tokens.push_back(token);
			bRead = false;
			bStuck = true;
		}
		
		if(ch == ':')
		{
			token.type = Token::Colon;
			token.value = ch;
			token.lineNum = lineNum;
			token.colNum = colNum;
			
			tokens.push_back(token);
			bRead = true;
			bStuck = false;
		}
		
		if(ch == ',')
		{
			token.type = Token::Comma;
			token.value = ch;
			token.lineNum = lineNum;
			token.colNum = colNum;
			
			tokens.push_back(token);
			bRead = true;
			bStuck = false;
		}
		
		if(ch == '=')
		{
			token.type = Token::Equal;
			token.value = ch;
			token.lineNum = lineNum;
			token.colNum = colNum;
			
			tokens.push_back(token);
			bRead = true;
			bStuck = false;
		}
		
		if(ch == '/')
		{
			while(ch != '\n' && ch != EOF)
			{
				ch = (char)fgetc(pFile);
				colNum++;
			}
			bRead = false;
			bStuck = true;
		}
		
		if(ch == '\n')
		{
			token.type = Token::EndOfLine;
			token.value = ch;
			token.lineNum = lineNum;
			token.colNum = colNum;
			
			tokens.push_back(token);
			
			lineNum++;
			colNum = 0;
			bRead = true;
			bStuck = false;
		}
		
		if(ch == ' ' || ch == '\t')
		{
			bRead = true;
			bStuck = false;
		}
	}
	
	token.type = Token::EndOfFile;
	token.value = "EOF";
	token.lineNum = lineNum;
	token.colNum = colNum;
			
	tokens.push_back(token);
	
	fclose(pFile);
	
	//
	// Parse Tokens
	//
	
	std::vector<ProgramLine> ProgramLines;
	std::vector<Label> Labels;
	std::vector<Variable> Variables;
	
	ProgramLine programLine;
	int programLineNum = 0;
	
	Label label;
	Variable variable;
	
	for(i=0;i<tokens.size();i++)
	{
		if(tokens[i].type == Token::Identifier)
		{
			if(tokens[i+1].type == Token::Colon) // It's a label
			{
				label.name = tokens[i].value;
				label.line = programLineNum;
				
				Labels.push_back(label);
				
				i += 1;
				
				continue;
			}
			else if(tokens[i].value == "STOP" && (tokens[i+1].type == Token::EndOfLine || tokens[i+1].type == Token::EndOfFile)) // It's a single command
			{
				programLine.lineNum = tokens[i].lineNum;
			
				programLine.output = "0";
				programLine.time = "1";
				programLine.timeunit = "US";
				programLine.command = "STOP";
				programLine.data = "0";
				
				ProgramLines.push_back(programLine);
				programLineNum++;
				
				i++;
			}
			else // Otherwise Error
			{
				outputStream<<"Expecting output pattern on line "<<tokens[i].lineNum<<" starting at column "<<tokens[i].colNum<<'.'<<std::endl;
				outputStream<<"Got "<<Convert(tokens[i].value)<<'.'<<std::endl;
				if(tokens[i].value == "STOP")
					outputStream<<"STOP should be followed by End of Line."<<std::endl;
				return 0;
			}
		}

		if(tokens[i].type == Token::Variable && tokens[i+1].type == Token::Equal)
		{
			if(tokens[i+2].type != Token::Identifier && tokens[i+2].type != Token::Numeric)
			{
				outputStream<<"Expecting value after "<<tokens[i+1].value<<" on line "<<tokens[i+1].lineNum<<" starting at column "<<tokens[i+1].colNum<<'.'<<std::endl;
				outputStream<<"Got "<<Convert(tokens[i+2].value)<<'.'<<std::endl;
				return 0;
			}
			
			bool bFound = false;
			unsigned int j;
			for(j=0;j<Variables.size();j++)
				if(Variables[j].name == tokens[i].value)
				{
					Variables[j].value = tokens[i+2].value;
					bFound = true;
				}
				
			if(!bFound)
			{
				variable.name = tokens[i].value;
				variable.value = tokens[i+2].value;
				Variables.push_back(variable);
			}
			
			i += 3;
		}
		
		if(tokens[i].type == Token::Numeric || tokens[i].type == Token::Variable) // Program Line
		{
			unsigned int j;
			bool bFound;
			if(tokens[i].type == Token::Variable)
			{
				bFound = false;
			
				for(j=0;j<Variables.size();j++)
					if(Variables[j].name == tokens[i].value)
					{
						tokens[i].type = Token::Numeric;
						tokens[i].value = Variables[j].value;
						bFound = true;
					}
					
				if(!bFound)
				{
					outputStream<<"Unknown variable "<<tokens[i].value<<" on line "<<tokens[i].lineNum<<" starting at column "<<tokens[i].colNum<<'.'<<std::endl;
					outputStream<<"Variables must be declared beforehand."<<std::endl;
					return 0;
				}
			}
			
			programLine.lineNum = tokens[i].lineNum;
			programLine.output = tokens[i].value;
			
			if(tokens[i+1].type != Token::Comma) // No comma
			{
				outputStream<<"Expecting comma after "<<tokens[i].value<<" on line "<<tokens[i].lineNum<<" starting at column "<<tokens[i].colNum<<'.'<<std::endl;
				outputStream<<"Got "<<Convert(tokens[i+1].value)<<'.'<<std::endl;
				outputStream<<"Check for bad output pattern."<<std::endl;
				return 0;
			}
			
			i+=2;
			
			if(tokens[i].type == Token::Variable)
			{
				bFound = false;
			
				for(j=0;j<Variables.size();j++)
					if(Variables[j].name == tokens[i].value)
					{
						tokens[i].type = Token::Numeric;
						tokens[i].value = Variables[j].value;
						bFound = true;
					}
					
				if(!bFound)
				{
					outputStream<<"Unknown variable "<<tokens[i].value<<" on line "<<tokens[i].lineNum<<" starting at column "<<tokens[i].colNum<<'.'<<std::endl;
					outputStream<<"Variables must be declared beforehand."<<std::endl;
					return 0;
				}
			}
			
			if(tokens[i].type != Token::Numeric) // No time field
			{
				outputStream<<"Expecting time field after "<<tokens[i-1].value<<" on line "<<tokens[i-1].lineNum<<" starting at column "<<tokens[i-1].colNum<<'.'<<std::endl;
				outputStream<<"Got "<<Convert(tokens[i].value)<<'.'<<std::endl;
				return 0;
			}
			
			programLine.time = "";
			
			j = 0;
			while(isdigit(tokens[i].value[j]) || tokens[i].value[j] == '.')
				programLine.time += tokens[i].value[j++];
							
			tokens[i].value.erase(0, j);
					
			programLine.timeunit = tokens[i].value;
			
			if(programLine.timeunit == "")
			{
				outputStream<<"Expecting time units after "<<tokens[i].value<<" on line "<<tokens[i].lineNum<<" starting at column "<<tokens[i].colNum<<'.'<<std::endl;
				outputStream<<"Got "<<Convert(programLine.timeunit)<<'.'<<std::endl;
				return 0;
			}
			
			i += 1;
			
			if(tokens[i].type != Token::Comma) // No comma
			{
				programLine.command = "CONTINUE";
				programLine.data = "0";
			}
			else
			{
				if(tokens[i+1].type == Token::Variable)
				{
					bFound = false;
				
					for(j=0;j<Variables.size();j++)
						if(Variables[j].name == tokens[i+1].value)
						{
							tokens[i+1].type = Token::Identifier;
							tokens[i+1].value = Variables[j].value;
							bFound = true;
						}
						
					if(!bFound)
					{
						outputStream<<"Unknown variable "<<tokens[i+1].value<<" on line "<<tokens[i+1].lineNum<<" starting at column "<<tokens[i+1].colNum<<'.'<<std::endl;
						outputStream<<"Variables must be declared beforehand."<<std::endl;
						return 0;
					}
				}
			
				if(tokens[i+1].type != Token::Identifier)
				{
					outputStream<<"Expecting command after "<<tokens[i].value<<" on line "<<tokens[i].lineNum<<" starting at column "<<tokens[i].colNum<<'.'<<std::endl;
					outputStream<<"Got "<<Convert(tokens[i+1].value)<<'.'<<std::endl;
					return 0;
				}
				
				programLine.command = tokens[i+1].value;
				
				i += 2;
				
				programLine.data = "0";
				
				if(programLine.command == "BRANCH" || programLine.command == "JSR")
				{
					if(tokens[i].type != Token::Comma)
					{
						outputStream<<"Expecting comma after "<<tokens[i-1].value<<" on line "<<tokens[i-1].lineNum<<" starting at column "<<tokens[i-1].colNum<<'.'<<std::endl;
						outputStream<<"Got "<<Convert(tokens[i].value)<<'.'<<std::endl;
						return 0;
					}
					
					if(tokens[i+1].type == Token::Variable)
					{
						bFound = false;
					
						for(j=0;j<Variables.size();j++)
							if(Variables[j].name == tokens[i+1].value)
							{
								tokens[i+1].type = Token::Identifier;
								tokens[i+1].value = Variables[j].value;
								bFound = true;
							}
							
						if(!bFound)
						{
							outputStream<<"Unknown variable "<<tokens[i+1].value<<" on line "<<tokens[i+1].lineNum<<" starting at column "<<tokens[i+1].colNum<<'.'<<std::endl;
							outputStream<<"Variables must be declared beforehand."<<std::endl;
							return 0;
						}
					}
					
					if(tokens[i+1].type != Token::Identifier)
					{
						outputStream<<"Expecting label after "<<tokens[i].value<<" on line "<<tokens[i].lineNum<<" starting at column "<<tokens[i].colNum<<'.'<<std::endl;
						outputStream<<"Got "<<Convert(tokens[i+1].value)<<'.'<<std::endl;
						return 0;
					}
					
					programLine.data = tokens[i+1].value;
					
					i += 2;
				}
				else if(tokens[i].type == Token::Comma)
				{
					if(tokens[i+1].type == Token::EndOfLine || tokens[i+1].type == Token::EndOfFile)
					{
						outputStream<<"Expecting data after "<<tokens[i].value<<" on line "<<tokens[i].lineNum<<" starting at column "<<tokens[i].colNum<<'.'<<std::endl;
						outputStream<<"Got "<<Convert(tokens[i+1].value)<<'.'<<std::endl;
						return 0;
					}
					
					if(tokens[i+1].type == Token::Variable)
					{
						bFound = false;
					
						for(j=0;j<Variables.size();j++)
							if(Variables[j].name == tokens[i+1].value)
							{
								tokens[i+1].type = Token::Numeric;
								tokens[i+1].value = Variables[j].value;
								bFound = true;
							}
							
						if(!bFound)
						{
							outputStream<<"Unknown variable "<<tokens[i+1].value<<" on line "<<tokens[i+1].lineNum<<" starting at column "<<tokens[i+1].colNum<<'.'<<std::endl;
							outputStream<<"Variables must be declared beforehand."<<std::endl;
							return 0;
						}
					}
					
					programLine.data = tokens[i+1].value;
					
					i += 2;
				}
			}
						
			ProgramLines.push_back(programLine);
			programLineNum++;
		}
		
		if(tokens[i].type != Token::EndOfLine && tokens[i].type != Token::EndOfFile)
		{
			outputStream<<"Expecting end of line after "<<tokens[i-1].value<<" on line "<<tokens[i-1].lineNum<<" starting at column "<<tokens[i-1].colNum<<'.'<<std::endl;
			outputStream<<"Got "<<Convert(tokens[i].value)<<'.'<<std::endl;
			return 0;
		}
	}
	
	if(bDebug)
	{
		outputStream<<"Labels:"<<std::endl;
		for(i=0;i<Labels.size();i++)
			outputStream<<Labels[i].name<<" = "<<Labels[i].line<<std::endl;
		outputStream<<std::endl;
	}
	
	if(bDebug)
	{
		outputStream<<"Variables:"<<std::endl;
		for(i=0;i<Variables.size();i++)
			outputStream<<Variables[i].name<<std::endl;
		outputStream<<std::endl;
	}
	
	if(bDebug)
	{
		outputStream<<"Program Lines:"<<std::endl;
		for(i=0;i<ProgramLines.size();i++)
			outputStream<<"Line "<<i+1<<": "<<ProgramLines[i].output<<", "<<ProgramLines[i].time<<ProgramLines[i].timeunit<<", "<<ProgramLines[i].command<<", "<<ProgramLines[i].data<<std::endl;
		outputStream<<std::endl;
	}
	
	//
	// Program Board
	//
	
	int output;
	double time;
	double timeunit;
	int command;
	int data;
	
	unsigned int instCount = 0;
	
	std::stack<int> LoopStack;
	
	// Init board
    if(pb_init() != 0)
    {
        outputStream<<"PulseBlaster board not found."<<std::endl;
		return 0;
    }
	
	outputStream<<"Using Clock Frequency of "<<frequency<<" MHz."<<std::endl<<std::endl;
	pb_core_clock(frequency);  // tell driver the clock frequency
	
	if(bDebug)
		outputStream<<"Parse Values:"<<std::endl;
	
	pb_start_programming(PULSE_PROGRAM);
	
	for(i=0;i<ProgramLines.size();i++)
	{
		if(ProgramLines[i].output[1] == 'B')
		{
			if(!BinaryStringToInteger(ProgramLines[i].output.c_str()+2, &output))
			{
				outputStream<<std::endl<<"Output value on line "<<ProgramLines[i].lineNum<<" is invalid."<<std::endl;
				outputStream<<'\t'<<ProgramLines[i].output<<std::endl;
				pb_stop_programming();
				pb_close();
				return 0;
			}
		}
		else if(ProgramLines[i].output[1] == 'X')
		{
			if(!HexStringToInteger(ProgramLines[i].output.c_str()+2, &output))
			{
				outputStream<<std::endl<<"Output value on line "<<ProgramLines[i].lineNum<<" is invalid."<<std::endl;
				outputStream<<'\t'<<ProgramLines[i].output<<std::endl;
				pb_stop_programming();
				pb_close();
				return 0;
			}
		}
		else if(ProgramLines[i].output[1] == 'N')
		{
			if(!NaturalLanguage(ProgramLines[i].output.c_str()+2, &output))
			{
				outputStream<<std::endl<<"Output value on line "<<ProgramLines[i].lineNum<<" is invalid."<<std::endl;
				outputStream<<'\t'<<ProgramLines[i].output<<std::endl;
				pb_stop_programming();
				pb_close();
				return 0;
			}
		}
		else
		{
			unsigned int j;
			for(j=0;j<ProgramLines[i].output.size();j++)
				if(!isdigit(ProgramLines[i].output[j]))
				{
					outputStream<<std::endl<<"Output value on line "<<ProgramLines[i].lineNum<<" is invalid."<<std::endl;
					outputStream<<'\t'<<ProgramLines[i].output<<std::endl;
					pb_stop_programming();
					pb_close();
					return 0;
				}
				
			output = atoi(ProgramLines[i].output.c_str());
		}
	
		time = atof(ProgramLines[i].time.c_str());
		
		if(ProgramLines[i].timeunit == "S")
			timeunit = 1000000000.0;
		else if(ProgramLines[i].timeunit == "MS")
			timeunit = ms;
		else if(ProgramLines[i].timeunit == "US")
			timeunit = us;
		else if(ProgramLines[i].timeunit == "NS")
			timeunit = ns;
		else // Invalid time unit
		{
			outputStream<<std::endl<<"Time unit on line "<<ProgramLines[i].lineNum<<" is invalid."<<std::endl;
			outputStream<<'\t'<<ProgramLines[i].timeunit<<std::endl;
			pb_stop_programming();
			pb_close();
			return 0;
		}
		
		command = CommandLookup(ProgramLines[i].command.c_str());
		
		if(command == LOOP)
			LoopStack.push(i);
		
		if(command == -1)
		{
			outputStream<<std::endl<<"Command on line "<<ProgramLines[i].lineNum<<" is invalid."<<std::endl;
			outputStream<<'\t'<<ProgramLines[i].command<<std::endl;
			pb_stop_programming();
			pb_close();
			return 0;
		}
		
		if(command == BRANCH || command == JSR)
		{
			data = -1;
		
			for(unsigned int j=0;j<Labels.size();j++)
				if(Labels[j].name == ProgramLines[i].data)
					data = Labels[j].line;
			
			if(data == -1)
			{
				outputStream<<std::endl<<"Unknown label on line "<<ProgramLines[i].lineNum<<':'<<std::endl;
				outputStream<<'\t'<<ProgramLines[i].data<<std::endl;
				pb_stop_programming();
				pb_close();
				return 0;
			}
		}
		else if(command == END_LOOP)
		{
			if(LoopStack.size() == 0)
			{
				outputStream<<std::endl<<"END_LOOP without LOOP on line "<<ProgramLines[i].lineNum<<'.'<<std::endl;
				pb_stop_programming();
				pb_close();
				return 0;
			}
			
			data = LoopStack.top();
			LoopStack.pop();
		}
		else
		{
			data = atoi(ProgramLines[i].data.c_str());
		}
		
		if(bDebug)
			outputStream<<"Line "<<i+1<<": "<<output<<" "<<time*timeunit<<" "<<command<<" "<<data<<std::endl;
		
		if(pb_inst(output, command, data, time*timeunit) < 0)
		{
			outputStream<<std::endl<<"Failed writing instruction on Line "<<ProgramLines[i].lineNum<<" to board."<<std::endl;
			outputStream<<pb_get_error()<<std::endl;
			pb_stop_programming();
			pb_close();
			return 0;
		}
		
		instCount++;
	}
	
	pb_stop_programming();
	
	pb_close(); // Release Board
	
	outputStream<<std::endl<<instCount<<" instructions interpreted."<<std::endl;
	outputStream<<"Board programmed successfully."<<std::endl;
	
	return 1;
}
