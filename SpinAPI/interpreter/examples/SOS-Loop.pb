// Sample program for SpinCore PulseBlaster Interpreter.
// SOS using loops.

// 3 Short			
start: 0xFFFFFF, 100ms, LOOP, 3
       0x000000, 100ms, END_LOOP
			
// 3 Long
       0xFFFFFF, 300ms, LOOP, 3
       0x000000, 100ms, END_LOOP
			
// 3 Short			
       0xFFFFFF, 100ms, LOOP, 3
       0x000000, 100ms, END_LOOP
			
// A pause
       0x000000, 500ms, branch, start // branch to start