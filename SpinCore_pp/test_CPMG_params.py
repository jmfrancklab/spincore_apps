SW_kHz = 75.0
nPoints = 128
transient = 500.
acq_time = nPoints/SW_kHz
tau = transient + acq_time*1e3*0.5
pad = 2*tau - transient - acq_time*1e3

print acq_time,"ms"
print tau,"us"
print pad,"us"




