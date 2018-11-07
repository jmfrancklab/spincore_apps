#pragma once
#ifndef __DEBUG_H__
#define __DEBUG_H__

#define DEBUG_ERROR   0
#define DEBUG_WARNING 1
#define DEBUG_INFO    2

/**
 * \internal
 */
void _debug (unsigned int severity, const char* function, unsigned int lineno, const char *format, ...);

#define debug(SEVERITY, FORMAT, ...) _debug(SEVERITY, __FUNCTION__, __LINE__, FORMAT, ##__VA_ARGS__)

#endif /*__DEBUG_H__*/
