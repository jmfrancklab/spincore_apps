#ifndef _INTERPRETER_H_
#define _INTERPRETER_H_

#pragma once

#include <string>
#include <sstream>

#define INTERPRETER_VERSION "PulseBlaster Interpreter\r\nCopyright SpinCore Technologies, Inc. 2016\r\n"

int Interpret(double frequency, char *filename, std::ostream& outputStream, bool bDebug = false);

#endif
