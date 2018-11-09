#ifndef __PULSEBLASTER_H__
#define __PULSEBLASTER_H__

#ifndef SPINCORE_API
#define SPINCORE_API
#endif

//Defines for start_programming
#define PULSE_PROGRAM  0

//Defines for using different units of time
#define ns 1.0
#define us 1000.0
#define ms 1000000.0

//Defines for status bits
#define STATUS_STOPPED  1
#define STATUS_RESET    2
#define STATUS_RUNNING  4
#define STATUS_WAITING  8

//Defines for different pb_inst instruction types
#define CONTINUE 0
#define STOP 1
#define LOOP 2
#define END_LOOP 3
#define JSR 4
#define RTS 5
#define BRANCH 6
#define LONG_DELAY 7
#define WAIT 8
#define RTI 9

#ifdef PB24
#define pb_inst pb_inst_pbonly
#endif

#ifdef PBESR
#define pb_inst pb_inst_pbonly
#endif

#ifdef PBESRPRO
#define pb_inst pb_inst_pbonly
#endif

#ifndef pb_inst
#define pb_inst pb_inst_pbonly64
#endif

#define ALL_FLAGS_ON	0x1FFFFF
#define ONE_PERIOD		0x200000
#define TWO_PERIOD		0x400000
#define THREE_PERIOD	0x600000
#define FOUR_PERIOD		0x800000
#define FIVE_PERIOD		0xA00000
#define SIX_PERIOD    0xC00000
#define ON				    0xE00000

#define REG_SHORTPULSE_DISABLE 	0x06
#define REG_START_ADDRESS 		0x07
#define REG_DEFAULT_FLAGS 		0x08

#ifdef __cplusplus
extern "C"
{
#endif
/**
 * This function is used to write a pulse program to any PulseBlaster QuadCore design 
 *
 *\param flag Output flag pattern for the current instruction.
 *\param length Length of the current instruction in nanoseconds.
 *
 *\return Returns 0 on success.
 *
 */
SPINCORE_API int pb_4C_inst(int flag, double length);
/**
 * This function is used to stop operation of a pulse program on the specified core
 * when using any PulseBlaster QuadCore design. 
 *
 *\return Returns 0 on success.
 *
 */
SPINCORE_API int pb_4C_stop(void);
/**
 * This is the instruction programming function for boards without a DDS. 
 * (for example PulseBlaster and PulseBlasterESR boards). Syntax is identical to that of
 * pb_inst_tworf(), except that the parameters pertaining to the analog outputs
 * are not used.
 */
SPINCORE_API int pb_inst_pbonly (unsigned int flags, int inst, int inst_data,
				                 double length);
/**
 * This is the instruction programming function for boards without a DDS. 
 * (for example PulseBlaster and PulseBlasterESR boards). Syntax is identical to that of
 * pb_inst_tworf(), except that the parameters pertaining to the analog outputs
 * are not used.
 */
SPINCORE_API int pb_inst_pbonly64 (__int64 flags, int inst, int inst_data,
				   double length);
/**
 * This function allows you to directly specify the fields for an instruction, which will
 * then be passed directly to the board without any modification by software.
 * See your product manual for a discussion of the meaning of each field.
 * <p>
 * This function is provided mainly to help us debug the boards. It is highly 
 * recommended that users make use the higher level instruction functions such 
 * as pb_inst(), pb_inst_pbonly(), pb_inst_tworf(), pb_inst_radio(). These allow the
 * creation of instructions in a more user-friendly manner
 * and also perform additional error checking to help you avoid accidentally
 * using paramaters that are out of range for your board.
 *
 * \param flags Flag field
 * \param inst Instruction (4 bits)
 * \param inst_data_direct Instruction data (20 bits) Unlike the other pb_inst*
 * instructions, this field is passed directly to the board and not adjusted based
 * on the instruction used. (eg, using a value of 2 for a loop instruction will cause
 * 3 loops to happen. The other pb_inst* functions would modify this value so the
 * number of loops entered is the number produced)
 * \param length Delay field (32 bits) Note that this is the value is NOT the number
 * of clock cycles an instruction will execute for. There is typically an additional
 * fixed internal delay which is added to produce the actual delay.
 */
SPINCORE_API int pb_inst_direct (const int *pflags, int inst, int inst_data_direct, int length);

/**
 * This function allows you to modify the behaviour of the PB CORE counter fix.
 * Do not use this function unless advised to do so.
 * \param option Set to 0 to turn on the fix, 1 to turn it off.
 */
SPINCORE_API void pb_bypass_FF_fix (int option);

/**
 *This function is for PBESR-PRO-II designs. It allows for 24 bit operation.
 *<p>
 *This function expects standard ASCII input characters ('1' is ASCII 49, '0' is ASCII 48). 
 *If you have an international version of Windows that uses a character set other
 *than ASCII, you may need to modify this function.
 *\param Flags String of 24 1s and 0s corresponding to the 24 flag bits(from left to
 * right: Channel 23, Channel 22, Channel 21, ... , Channel 0)
 *\param length Floating point number, representing the desired pulse length, in nanoseconds
 *\return The number of clock cycles used is returned on success.
 */
SPINCORE_API int pb_inst_hs24(const char* Flags, double length);

// PulseBlasterESR-Pro-II functions
/**
 *This function is for PBESR-PRO-II designs. It allows for 8 bit operation.
 *<p>
 *This function expects standard ASCII input characters ('1' is ASCII 49, '0' is ASCII 48). 
 *If you have an international version of Windows that uses a character set other
 *than ASCII, you may need to modify this function.
 *\param Flags String of 8 1s and 0s corresponding to the 8 flag bits(from left to
 * right: Channel 7, Channel 6, Channel 5, etc.)
 *\param length Floating point number, representing the desired pulse length, in nanoseconds
 *\return A negative number is returned on failure. The number of clock cycles used is returned on success.
 *
 */
SPINCORE_API int pb_inst_hs8(const char* Flags, double length);

/**
*This function is for PulseBlaster-QuadCore designs. It is used to select which 
*PB-Core to access for the operations that follow it. See PB-Quad_Core manual 
*for more information.
*\param core_sel selects the appropriate core(s). Individual cores or groups of
* multiple cores can be selected as follows:
* <ul>
* <li>0x1 (binary: 0001) - Selects Core0.
* <li>0x2 (binary: 0010) - Selects Core1.
* <li>0x4 (binary: 0100) - Selects Core2.
* <li>0x8 (binary: 1000) - Selects Core3.
* <li>0xF (binary: 1111) - Selects all four cores.
* <li>etc.
* </ul>
*\return A negative number is returned on failure. 0 is returned on success.
*/
SPINCORE_API int pb_select_core (unsigned int core_sel);


/**
*This function is for PulseBlaster-ESR programmable fixed pulse designs. 
*It is used to set the period, pulse width and delay for Clock Outputs 0-3. 
*\param channel selects the appropriate channel. 
*\param period selects the appropriate period. 
*\param pulse_width selects the appropriate pulse width. 
*\param delay selects the appropriate delay. 
*/
SPINCORE_API int pb_set_pulse_regs (unsigned int channel, double period, double clock_high, double offset);
  
#ifdef __cplusplus
}
#endif


#endif /*__PULSEBLASTER_H__*/
