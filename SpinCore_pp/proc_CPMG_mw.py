from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping,nnls
fl = figlist_var()
rcParams['figure.figsize'] = [10,6]


# 


date,id_string = '190609','CPMG_DNP_1'


# 


SW_kHz = 9.0
nPoints = 128
nEchoes = 64
nPhaseSteps = 2 
filename = date+'_'+id_string+'.h5'
nodename = 'signal'
s = nddata_hdf5(filename+'/'+nodename,
        directory = getDATADIR(
            exp_type = 'test_equip'))
s.set_units('t','s')
print ndshape(s)


# 


fl.next(id_string+'raw data ')
fl.image(s)


# 


orig_t = s.getaxis('t')
p90_s = 4.1*1e-6
deadtime_s = 100.0*1e-6
deblank = 1.0*1e-6
acq_time_s = orig_t[nPoints]
tau_s = deadtime_s + acq_time_s*0.5
pad_s = 2.0*tau_s - deadtime_s - acq_time_s - 2.0*p90_s - deblank
tE_s = 2.0*p90_s + deadtime_s + acq_time_s + pad_s
print "ACQUISITION TIME:",acq_time_s,"s"
print "TAU DELAY:",tau_s,"s"
print "TWICE TAU:",2.0*tau_s,"s"
print "ECHO TIME:",tE_s,"s"
t2_axis = linspace(0,acq_time_s,nPoints)
tE_axis = r_[1:nEchoes+1]*tE_s
s.setaxis('t',None)
s.chunk('t',['ph1','tE','t2'],[nPhaseSteps,nEchoes,-1])
s.setaxis('ph1',r_[0.,2.]/4)
#tE_axis = r_[1:nEchoes+1]*tE_s
s.setaxis('tE',tE_axis)
s.setaxis('t2',t2_axis)
fl.next(id_string+'raw data - chunking')
fl.image(s)
s.ft('t2', shift=True)
fl.next(id_string+'raw data - chunking ft')
fl.image(s)


# 


s.ft(['ph1'])
fl.next(id_string+' image plot coherence-- ft ')
fl.image(s)
s.ift('t2')
fl.next(id_string+' image plot coherence ')
fl.image(s)


# 


s = s['ph1',1].C
fl.next(id_string+' image plot signal')
fl.image(s)


# 


echo_center = abs(s)['power',0]['tE',0].argmax('t2').data.item()
s.setaxis('t2', lambda x: x-echo_center)
s.rename('tE','nEchoes').setaxis('nEchoes',r_[1:nEchoes+1])
fl.next('check center')
fl.image(s)


# 


s.ft('t2')
fl.next('before phased - real ft')
fl.image(s.real)
fl.next('before phased - imag ft')
fl.image(s.imag)


# 


f_axis = s.fromaxis('t2')
def costfun(p):
    zeroorder_rad,firstorder = p
    phshift = exp(-1j*2*pi*f_axis*(firstorder*1e-6))
    phshift *= exp(-1j*2*pi*zeroorder_rad)
    corr_test = phshift * s
    return (abs(corr_test.data.imag)**2)[:].sum()
iteration = 0
def print_fun(x, f, accepted):
    global iteration
    iteration += 1
    print (iteration, x, f, int(accepted))
    return
sol = basinhopping(costfun, r_[0.,0.],
        minimizer_kwargs={"method":'L-BFGS-B'},
        callback=print_fun,
        stepsize=100.,
        niter=100,
        T=1000.
        )
zeroorder_rad, firstorder = sol.x
phshift = exp(-1j*2*pi*f_axis*(firstorder*1e-6))
phshift *= exp(-1j*2*pi*zeroorder_rad)
s *= phshift
print "RELATIVE PHASE SHIFT WAS {:0.1f}\us and {:0.1f}$^\circ$".format(
        firstorder,angle(zeroorder_rad)/pi*180)


# 


#if s['power',-1]['nEchoes',0].data[:].sum().real > 0:
#    s *= -1
s *= -1.0


# 


print ndshape(s)
fl.next('after phased - real ft')
fl.image(s.real)
fl.next('after phased - imag ft')
fl.image(s.imag)
s.ift('t2')
fl.next('after phased - real')
fl.image(s.real)
fl.next('after phased - imag')
fl.image(s.imag)
s.ft('t2')


# 


print ndshape(s)


# 


s.reorder('nEchoes',first=False)


# 


fl.next('Echoes at maximum power')
fl.plot(s['power',-1]['t2':(-500,900)])


# 


s.reorder('t2',first=False)
s.rename('nEchoes','tE').setaxis('tE',tE_axis)
data = s['t2':(-500,900)].C
fl.next('sliced, after phased - real')
fl.image(data)
fl.next('sliced, after phased - imag')
fl.image(data)


# 


data = data.real.C.sum('t2')


# 


power_list = s.getaxis('power')
amplitude_r = empty_like(power_list)
T2_r = empty_like(power_list)


# 


for i,k in enumerate(power_list):
    temp = data['power',i].C
    x = tE_axis 
    ydata = temp.data.real
    fl.next('DECAY DATA')
    fl.plot(x,ydata, '.', alpha=0.4, label='%f'%k, human_units=False)
    fitfunc = lambda p, x: p[0]*exp(-x/p[1])
    errfunc = lambda p_arg, x_arg, y_arg: fitfunc(p_arg, x_arg) - y_arg
    p0 = [1000.0,0.6]
    p1, success = leastsq(errfunc, p0[:], args=(x, ydata))
    x_fit = linspace(x.min(),x.max(),20000)
    fl.next('DECAY FITS')
    fl.plot(x_fit, fitfunc(p1, x_fit),':', label='fit (T2 = %0.2f ms)'%(p1[1]*1e3), human_units=False)
    xlabel('t (sec)')
    ylabel('Intensity')
    print "FOR POWER:",power_list[i],"W \tAMPLITUDE:",p1[0],"\tT2:",p1[1]
    amplitude_r[i] = p1[0]
    T2_r[i] = p1[1]
    


# 


power_data = ndshape([len(power_list)],['power']).alloc()
power_data.setaxis('power',power_list).set_units('power','W')
power_data['power',:] = amplitude_r[:]
T2_data = ndshape([len(power_list)],['power']).alloc()
T2_data.setaxis('power',power_list).set_units('power','W')
T2_data['power',:] = T2_r[:]
baseline_p = power_data['power',0].data
corrected_p = power_data.C
corrected_p['power',:] = corrected_p.data/baseline_p
baseline_T2 = T2_data['power',0].data
corrected_T2 = T2_data.C
corrected_T2['power',:] = corrected_T2.data/baseline_T2
fl.next('CPMG DNP, Enhancement vs power: 1.25 mM 4-AT')
fl.plot(corrected_p,'.',label='programmed power',human_units=False)
fl.next('T2 vs power: 1.25 mM 4-AT')
fl.plot(corrected_T2,'.')
    


# 


rx_list = s.get_prop('rx_array')
rx_list[0] = 0
rx_r = zeros(len(rx_list)+1)
def convert_to_power(x):
    "Convert Rx mV values to powers (dBm)"
    y = 0
    c = r_[2.78135,25.7302,5.48909]
    for j in range(len(c)):
        y += c[j] * (x*1e-3)**(len(c)-j)
    return log10(y)*10.0+2.2
for x in xrange(len(rx_list)):
    #rx_r[x+1] = ((rx_list[x])**2/70000)*4
    rx_r[x+1] = 1e-3*10**((convert_to_power(rx_list[x])+29)/10.)
rx_data = ndshape([len(rx_r)],['rx']).alloc()
rx_data.setaxis('rx',array(rx_r)).set_units('rx','W')
rx_data['rx',:] = amplitude_r[:]
baseline_rx = rx_data['rx',0].data
corrected_rx = rx_data.C
corrected_rx['rx',:] = corrected_rx.data/baseline_rx
fl.next('CPMG DNP, Enhancement vs power: 1.25 mM 4-AT')
fl.plot(corrected_rx,'.',label='Bridge 12 RX readout',human_units=False)

fl.show();quit()
