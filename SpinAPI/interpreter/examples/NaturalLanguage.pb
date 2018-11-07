// Sample program for SpinCore PulseBlaster Interpreter.
// Using Natural Language.

start: 0n 0 + 7, 100ms // Bits 0 and 7 on.
       0n 1 + 6, 100ms // Bits 1 and 6 on.
       0n 2 + 5, 100ms // Bits 2 and 5 on.
       0n 3 + 4, 100ms       
       0n 4 + 3, 100ms
       0n 5 + 2, 100ms
       0n 6 + 1, 100ms
       0n 7 + 0, 100ms, branch, start