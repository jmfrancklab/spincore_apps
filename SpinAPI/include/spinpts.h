#ifndef __SPINPTS_H__
#define __SPINPTS_H__

#ifndef SPINCORE_API
#define SPINCORE_API
#endif

#define ERROR_STR_SIZE	    25
#define	BCDBYTEMASK		    	0x0F0F0F0F

#define 	ID_MHz100		0x0
#define		ID_MHz10		0x1  
#define		ID_MHz1			0x2
#define 	ID_kHz100		0x3
#define		ID_kHz10		0x4
#define		ID_kHz1			0x5
#define 	ID_Hz100		0x6
#define		ID_Hz10			0x7
#define		ID_Hz1			0x8
#define 	ID_pHz			0x9
#define 	ID_latch   	0xA
#define   ID_UNUSED		0xF
 
#define	PHASE_INVALID		0x100
#define FREQ_ORANGE			0x101

#define	DWRITE_FAIL			  0x200
#define	DEVICE_OPEN_FAIL	0x201
#define NO_DEVICE_FOUND		0x202

typedef struct BCDFREQ {
	char bcd_MHz[3]; 
	char bcd_kHz[3]; 
	char bcd_Hz[3];  
	char bcd_pHz[3]; 
} BCDFREQ;

#ifdef __cplusplus
extern "C"
{
#endif

/**
 * Set the frequency and phase to the first available PTS Device. The PTSDevice parameter is optional. 
 * Specifying a PTS Device structure will include frequency and phase bounds checking when setting 
 * the device.
 *
 * \param frequency Double values (greater than 0.)
 * \param phase Must be equal to 0, 90, 180, 270
 * \param device (OPTIONAL) Pointer to PTSDevice structure. This argument can be NULL.
 * \return Returns 0 if no error occurred.
 *             If an error occurs, returns an error code defined in \link spinapi.h \endlink
 */
SPINCORE_API int set_pts(double maxFreq, int is160, int is3200, int allowPhase, int noPTS, double frequency, int phase);

/**
 * Set the frequency and phase to a specific PTS Device. The PTSDevice parameter is optional. Specifying a PTS Device structure will 
 * include frequency and phase bounds checking when setting the device.
 *
 * \param pts_index Which PTS device to set. 1 corresponds to the first available device, 2 to the second and so forth.
 * \param frequency Double values (greater than 0.)
 * \param phase Must be equal to 0, 90, 180, 270
 * \param device (OPTIONAL) Pointer to PTSDevice structure. This argument can be NULL.
 * \return Returns 0 if no error occurred.
 *             If an error occurs, returns an error code defined in \link spinapi.h \endlink
 */
 
SPINCORE_API int set_pts_ex(int pts_index, double maxFreq, int is160, int is3200, int allowPhase, int noPTS, double frequency, int phase);
//SPINCORE_API int  set_pts( double frequency );

/**
 * Decodes error codes defined in \link spinapi.h \endlink
 *
 * \return Returns a pointer to a C string containing the error description.
 */
SPINCORE_API const char* spinpts_get_error(void);
/**
 * Gets the current version of  the SpinPTS API being used.
 *
 * \return Returns a pointer to a C string containing the version string.
 */
SPINCORE_API const char* spinpts_get_version(void);

#ifdef __cplusplus
}
#endif

#endif /*__SPINPTS_H__*/
