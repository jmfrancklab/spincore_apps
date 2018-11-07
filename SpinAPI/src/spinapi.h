#ifndef __SPINAPI_H__
#define __SPINAPI_H__

#ifdef __GNUC__
#ifndef __int64
#define __int64 long long int
#endif
#endif

#ifndef __GCC__
#define __func__ __FUNCTION__
#endif

//if building windows dll, compile with -DDLL_EXPORTS flag
//if building code to use windows dll, no -D flag necessary
#if defined(WINDOWS) || defined(WIN32)
#ifdef DLL_EXPORTS
#define SPINCORE_API __declspec(dllexport)
#else
#define SPINCORE_API __declspec(dllimport)
#endif
// else if not on windows, SPINCORE_API does not mean anything
#else
#define SPINCORE_API
#endif

// maximum number of boards that can be supported
#define MAX_NUM_BOARDS 32
#define PARAM_ERROR -99

#ifdef __cplusplus
extern "C"
{
#endif

/**
 * Return the number of SpinCore boards present in your system.
 *
 * \return The number of boards present is returned. -1 is returned on error.
 *
 */
SPINCORE_API int pb_count_boards (void);

/**
 * If multiple boards from SpinCore Technologies are present in your system,
 * this function allows you to select which board to talk to. Once this function
 * is called, all subsequent commands (such as pb_init(), pb_core_clock(), etc.) will be
 * sent to the selected board. You may change which board is selected at any time.
 *
 * If you have only one board, it is not necessary to call this function.
 *
 * \param board_num Specifies which board to select. Counting starts at 0.
 * \return A negative number is returned on failure. 0 is returned on success
 */
SPINCORE_API int pb_select_board (int board_num);

/**
 * Initializes the board. This must be called before any other functions are
 * used which communicate with the board.
 * If you have multiple boards installed in your system, pb_select_board() may be called first to select
 * which board to initialize.
 *
 * \return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_init (void);

/**
 * Tell the library what clock frequency the board uses. This should be
 * called at the beginning of each program, right after you initialize the
 * board with pb_init(). Note that this does not actually set the clock
 * frequency, it simply tells the driver what frequency the board is using,
 * since this cannot (currently) be auto-detected.
 * <p>
 * Also note that this frequency refers to the speed at which the PulseBlaster
 * core itself runs. On many boards, this is different than the value printed
 * on the oscillator. On RadioProcessor devices, the A/D converter and the
 * PulseBlaster core operate at the same clock frequency.
 * \param clock_freq Frequency of the clock in MHz.
 */
SPINCORE_API void pb_core_clock (double clock_freq);

SPINCORE_API void pb_set_clock(double clock_freq);

/**
 * End communication with the board. This is generally called as the last line in a program.
 * Once this is called, no further communication can take place with the board
 * unless the board is reinitialized with pb_init(). However, any pulse program that
 * is loaded and running at the time of calling this function will continue to
 * run indefinitely.
 *
 * \return A negative number is returned on failure. 0 is returned on success.
 */
 
SPINCORE_API int pb_close (void);
/**
 * This function tells the board to start programming one of the onboard 
 * devices. For all the devices, the method of programming follows the
 * following form:<br> a call to pb_start_programming(), a call to one or more
 * functions which transfer the actual data, and a call to pb_stop_programming().
 * Only one device can be programmed at a time.
 * \param device
 * Specifies which device to start programming. Valid devices are:<ul>
 * <li>PULSE_PROGRAM - The pulse program will be programmed using one of the pb_inst* instructions.
 * <li>FREQ_REGS - The frequency registers will be programmed using the pb_set_freq() function. (DDS and RadioProcessor boards only)
 * <li>TX_PHASE_REGS - The phase registers for the TX channel will be programmed using pb_set_phase() (DDS and RadioProcessor boards only)
 * <li>RX_PHASE_REGS - The phase registers for the RX channel will be programmed using pb_set_phase() (DDS enabled boards only)
 * <li>COS_PHASE_REGS - The phase registers for the cos (real) channel (RadioProcessor boards only)
 * <li>SIN_PHASE_REGS - The phase registers for the sine (imaginary) channel (RadioProcessor boards only)
 * </ul>
 * \return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_start_programming (int device);

/**
 * Finishes the programming for a specific on-board devices which was started by pb_start_programming(). 
 *
 * \return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_stop_programming (void);

/**
 * Send a software trigger to the board. This will start execution of a pulse
 * program. It will also trigger a program which is currently paused due to
 * a WAIT instruction. Triggering can also be accomplished through hardware,
 * please see your board's manual for details on how to accomplish this.
 * \return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_start (void);

/**
 * Stops output of board. Analog output will return to ground, and TTL outputs
 * will  either remain in the same state they were in when the reset command 
 * was received or return to ground. This also resets the PulseBlaster so that
 * the PulseBlaster Core can be run again using pb_start() or a hardware trigger.
 * \return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_stop (void);

/**
 * Stops the output of board and resets the PulseBlaster Core. Analog output will 
 * return to ground, and TTL outputs will either remain in the same state they were 
 * in when the reset command was received or return to ground. This also resets the
 * PulseBlaster Core so that the board can be run again using pb_start() or a hardware
 * trigger.  Note: Either pb_reset() or pb_stop() must be called before pb_start() if
 * the pulse program is to be run from the beginning (as opposed to continuing from a
 * WAIT state).
 * \return A negative number is returned on failure. 0 is returned on success.
 */
SPINCORE_API int pb_reset (void);

/**
 * Write 1 byte to the given PCI I/O address.
 * This is a low level hardware access function.
 * \param address The I/O Register to write to
 * \param data The byte to write
 */
SPINCORE_API int pb_outp (unsigned int address, unsigned char data);

/**
 * Read 1 byte from the given PCI I/O address.
 * This is a low level hardware access function.
 * \param address The I/O Register to read
 * \return The byte requested is returned.
 */
SPINCORE_API char pb_inp (unsigned int address);

/**
 * Write a 32 bit (4 byte) word to the given PCI I/O address.
 * This is a low level hardware access function.
 * \param address The I/O Register to write to. This should be a multiple of 4.
 * \param data The word to write
 */
SPINCORE_API int pb_outw (unsigned int address, unsigned int data);

/**
 * Read a 32 bit (4 byte) word from the given PCI I/O address.
 * This is a low level hardware access function.
 * \param address The I/O Register to read. This should be a multiple of 4.
 * \return The word requested is returned.
 */
SPINCORE_API unsigned int pb_inw (unsigned int address);

/**
 * For ISA Boards only. Specify the base address of the board. If you have a
 * PCI board, any call to this function is ignored.
 * \param address base address of the ISA board
 */
SPINCORE_API void pb_set_ISA_address (int address);

/**
 * Many parameters to function in the API are given as full precision double
 * values, such as the length of an instruction, or the phase to be programmed
 * to a phase register. Since the hardware does not have the full precision
 * of a double value, the parameters are rounded to match the internal
 * precision. This function allows you to
 * see what to what value the parameters were rounded. 
 *
 *\return The last value rounded by the API. 
 *
 */
SPINCORE_API double pb_get_rounded_value (void);

/**
 * Read status from the board. Not all boards support this, see your manual.
 * Each bit of the returned integer indicates whether the board is in that
 * state. Bit 0 is the least significant bit.
 *<ul>
 *<li>Bit 0 - Stopped
 *<li>Bit 1 - Reset 
 *<li>Bit 2 - Running
 *<li>Bit 3 - Waiting
 *<li>Bit 4 - Scanning (RadioProcessor boards only)
 *</ul>
 *
 *Note on Reset Bit: The Reset Bit will be true as soon as the board is initialized. 
 *It will remain true until a hardware or software trigger occurs,
 *at which point it will stay false until the board is reset again.
 *
 *Note on Activation Levels: The activation level of each bit depends on the board, please see
 *your product's manual for details.
 *
 * Bits 5-31 are reserved for future use. It should not be assumed that these
 * will be set to 0.
 * \return Word that indicates the state of the current board as described above.
 */
SPINCORE_API int pb_read_status (void);

/**
 * Read status message from the board. Not all boards support this, see your manual.
 * The returned string will either have the board's status or an error message
 *
 * \return String containing the status message of the board.
 */
SPINCORE_API const char *pb_status_message(void);

/**
 * Get the version of this library. The version is a string in the form
 * YYYYMMDD.
 * \return A string indicating the version of this library is returned.
 */
SPINCORE_API const char *pb_get_version (void);

/**
 * \deprecated
 * Return the most recent error string. Anytime a function (such as pb_init(),
 * pb_start_programming(), etc.) encounters an error, this function will return
 * a description of what went wrong.
 *
 * \return A string describing the last error is returned. A string containing
 * "No Error" is returned if the last function call was successful.
 */
SPINCORE_API const char *pb_get_error (void);

/**
 * Retrieve the most recent error string into a buffer. Whenever an error code is returned,
 * this function will return a description of what went wrong.
 * 
 * \param 
 *
 */
SPINCORE_API int pb_get_last_error(char *buffer, unsigned int size);

/**
 * Get the firmware version on the board. This is not supported on all boards.
 *
 *\return Returns the firmware id as described above. A 0 is returned if the
 *firmware id feature is not available on this version of the board.
 */
SPINCORE_API int pb_get_firmware_id (void);

/**
 * This function allows you to pause execution of your software for a given
 * number of milliseconds, and behaves like the sleep() function found on
 * many operating systems. This is provided because the sleep() function is not
 * standard across all operating systems/programming environments.
 * <p>This function does *NOT* interact with the hardware or pulse program at all. It
 * simply provides a portable way to access a sleep function.
 *
 * \param milliseconds Number of milliseconds to sleep (pause program) for.
 *
 */
SPINCORE_API void pb_sleep_ms (int milliseconds);

/**
 * Enable debug log. When enabled, spinapi will generate a file called log.txt,
 * which contains some debugging information. This file is probably not very useful
 * for the end-user, but if you are encountering difficulty, it will help us to turn
 * debugging on and email us the log along with your support question.
 * \param debug Set to 1 to turn on debugging outputs, or 0 to turn off.
 */
SPINCORE_API int pb_set_debug (int debug);

#ifdef __cplusplus
}
#endif

#include "pulseblaster.h"
#include "dds.h"
#include "radioprocessor.h"
#include "spinpts.h"
 
#endif /*#ifndef _SPINAPI_H__*/
