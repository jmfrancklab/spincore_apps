// Sample program for SpinCore PulseBlaster Interpreter.
// Loop example.

BegLoop: 0xFFFFFF, 500ms, LOOP, 3  // A loop with 3 iterations
         0x000000, 500ms, END_LOOP // End of loop
                                   // Interpreter will match END_LOOP with LOOP         

         0x000000, 1ms // Ensure all bits are off
         STOP // Stop execution