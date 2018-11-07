// Sample program for SpinCore PulseBlaster Interpreter.
// Simple all on all off pattern.

label: 0b1111 1111 1111 1111 1111 1111, 500 ms // All bits on for 500 ms, Continue to next instruction
       0b0000 0000 0000 0000 0000 0000, 500 ms, branch, label // All bits off for 500 ms, branch to label