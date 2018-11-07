// Sample program for SpinCore PulseBlaster Interpreter.
// SOS using sub routines.

start: 0x000000, 1ms, JSR, short
       0x000000, 1ms, JSR, long
       0x000000, 1ms, JSR, short
       0x000000, 500ms, BRANCH, start

// 3 Short			
short: 0xFFFFFF, 100ms
       0x000000, 100ms
       0xFFFFFF, 100ms
       0x000000, 100ms
       0xFFFFFF, 100ms
       0x000000, 100ms, RTS
			
// 3 Long
long:  0xFFFFFF, 300ms
       0x000000, 100ms
       0xFFFFFF, 300ms
       0x000000, 100ms
       0xFFFFFF, 300ms
       0x000000, 100ms, RTS
