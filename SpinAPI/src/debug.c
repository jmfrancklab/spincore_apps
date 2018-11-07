#include <stdio.h>
#include <time.h>
#include <stdarg.h>
#include <string.h>
#include <stdlib.h>

#include "version.h"
#include "debug.h"
#include "spinapi.h"

#ifdef __WINDOWS__
#define __LOCALTIME_S__
#define __FOPEN_S__
#define __SPRINTF_S__
#define __STRNCPY_S__
#endif

#ifdef __STDC_LIB_EXT1__
#define __LOCALTIME_S__
#endif

static int _log_enabled = 0;
static char _log_file_name[32] = "log.txt";
static FILE* _log_fp = NULL;

char _last_error[512];

int _debug_write_header(FILE *fp);

int
_pb_debug_write_header(FILE *fp)
{
	char ftime[32];
	time_t t;
	
	fprintf(fp, "SpinCore Technologies, Inc. SpinAPI ver. %s\n", pb_get_version());
	
	time(&t);

#ifdef __LOCALTIME_S__
	{
		struct tm timeinfo;
		ftime[0] = '\0';

#ifdef __WINDOWS__
		if (localtime_s(&timeinfo, &t) == 0) {
			asctime_s(ftime, sizeof(ftime), &timeinfo);
		}
#else
		asctime_s(ftime, sizeof(ftime), localtime_s(&timeinfo, &t));
#endif
	}
#else
	{
		strftime (ftime, sizeof(ftime), "%H:%M:%S", localtime(&t));
	}
#endif

	fprintf(fp, "Logfile created: %s\n", ftime);
	fprintf(fp, "Markers: (I) info, (W) warning, (E) error.\n\n");
	fprintf(fp, "================================================================================================\n");
	fprintf(fp, "    %-8s %-28s %-29s\n", "TIME", "FUNCTION" , "MESSAGE");
	fprintf(fp, "================================================================================================\n");

	return 0;
}

int 
pb_set_debug(int debug)
{
	_log_enabled = debug;
	return 0;
}

void 
_debug (unsigned int severity, const char* function, unsigned int lineno, const char *format, ...)
{
	char ftime[10];
	char fnbuf[64];

	time_t t;
	va_list ap;

	if(!_log_enabled) return;
	
	if(_log_fp == NULL) {

#ifdef __FOPEN_S__
		fopen_s(&_log_fp, _log_file_name, "w");
#else
		_log_fp = fopen(_log_file_name, "w");
#endif
		if(_log_fp == NULL) _log_fp = stdout;
		_pb_debug_write_header(_log_fp);
	}

	fprintf(_log_fp, "(");
	switch(severity) {
		case DEBUG_INFO:
			fprintf(_log_fp, "I");
			break;
		case DEBUG_WARNING:
			fprintf(_log_fp, "W");
			break;
		case DEBUG_ERROR:
			fprintf(_log_fp, "E");
			break;
		default:
			fprintf(_log_fp, "?");
	}
	fprintf(_log_fp, ") ");

	time(&t);

#ifdef __LOCALTIME_S__
	{
		struct tm timeinfo;

		if (localtime_s(&timeinfo, &t) == 0) {
			strftime(ftime, sizeof(ftime), "%H:%M:%S", &timeinfo);
		}
	}
#else
	strftime(ftime, sizeof(ftime), "%H:%M:%S", localtime(&t));
#endif

	va_start (ap, format);

#ifdef __SPRINTF_S__
	sprintf_s(fnbuf, sizeof(fnbuf), "%s:%d", function, lineno);
#else
	sprintf(fnbuf, sizeof(fnbuf), "%s:%d", function, lineno);
#endif

	fprintf (_log_fp, "%s %-28s", ftime, fnbuf);
	
	if(severity == DEBUG_ERROR) {
		vsnprintf(_last_error, sizeof(_last_error), format, ap);
		fprintf (_log_fp, "%s\n", _last_error);
	}
	else {
		vfprintf (_log_fp, format, ap);
		fprintf (_log_fp, "\n");
	}
	
	va_end (ap);

	fflush (_log_fp);
}

int 
pb_get_last_error(char *buffer, unsigned int size)
{
#ifdef __STRNCPY_S__
	strncpy_s(buffer, size, _last_error, 512);
#else
	strncpy(buffer, _last_error, size);
#endif
	return 0;
}

const char* 
pb_get_error(void)
{
	//debug(DEBUG_WARNING, "This function is deprecated; please use pb_get_last_error(..)");
	return _last_error;
}
