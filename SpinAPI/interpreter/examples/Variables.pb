// Sample program for SpinCore PulseBlaster Interpreter.
// Variable usage.

// Change the following values to change the program.
$output1 = 0xFFFFFF // Output pattern for Line 1
$output2 = 0x000000 // Output pattern for Line 2
$time1 = 500ms // Time value for Line 1
$time2 = 100ms // Time value for Line 2
$NumberOfLoops = 3 // Number of times to loop

start: $output1, $time1, loop, $NumberOfLoops
       $output2, $time2, end_loop
       0x000000, 1ms
       stop