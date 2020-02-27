SW_kHz = 64.0
nPoints = 128
trans = 500.0*1e-6
ACQ = SW_kHz/nPoints


transient = 500.
acq_time = nPoints/SW_kHz
tau = transient + acq_time*1e3*0.5
pad = 2*tau - transient - acq_time*1e3

print(acq_time,"ms")
print(tau,"us")
print(pad,"us")




