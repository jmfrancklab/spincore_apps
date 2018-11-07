// Sample program for SpinCore PulseBlaster Interpreter.
// Simple all on all off pattern.

label: 0b0000 0000 0000 0000 0000 0000, 1 ms  //Start with all bits off
       0b0000 0000 0000 0000 0000 0000, 5000 ms, wait  // Wait for a trigger to occur, then delay 5s before proceeding
       0b1111 1111 1111 1111 1111 1111, 500 ms, branch, label // All bits on for 500 ms, branch to label