
# coding: utf-8

# 


from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping,nnls
fl = figlist_var()
rcParams['figure.figsize'] = [10,6]


# 


date,id_string = '190630','CPMG_DNP_E_test_1'


# 


filename = date+'_'+id_string+'.h5'
nodename = 'signal'
s = nddata_hdf5(filename+'/'+nodename,
        directory = getDATADIR(
            exp_type = 'test_equip'))
SW_kHz = s.get_prop('acq_params')['SW_kHz']
nPoints = s.get_prop('acq_params')['nPoints']
nEchoes = s.get_prop('acq_params')['nEchoes']
nPhaseSteps = s.get_prop('acq_params')['nPhaseSteps']
s.set_units('t','s')
print ndshape(s)


# 


fl.next(id_string+'raw data ')
fl.image(s)


# 


def convert_to_power(x,which_cal='Rx'):
    "Convert Rx mV values to powers (dBm)"
    "Takes values in units of mV and converts to dBm"
    y = 0
    if which_cal == 'Rx':
        c = r_[2.78135,25.7302,5.48909]
    elif which_cal == 'Tx':
        c =r_[5.6378,38.2242,6.33419]
    for j in range(len(c)):
        y += c[j] * (x*1e-3)**(len(c)-j)
    return log10(y)*10.0+2.2

#tx_mon = r_[0.0,0.0,1.66e-3,2.33e-3,4.33e-3,9.66e-3,18.3e-3,35.0e-3,61.6e-3,90e-3,135e-3,176e-3,221e-3,236e-3,268e-3,293e-3,
#           343e-3,371e-3,406e-3,426e-3,460e-3,486e-3,533e-3,563e-3]
#tx_mon_corr = zeros_like(tx_mon)
#for x in xrange(len(tx_mon)):
#    tx_mon_corr[x] = 1e-3*10**((convert_to_power(tx_mon[x],'Tx')+29)/10.)


# 


#s.setaxis('power',tx_mon_corr*1e3)
#print s.getaxis('power')


# 


orig_t = s.getaxis('t')
p90_s = s.get_prop('acq_params')['p90_us']*1e-6
deadtime_s = s.get_prop('acq_params')['deadtime_us']*1e-6
deblank = s.get_prop('acq_params')['deblank_us']*1e-6
acq_time_s = orig_t[nPoints]
tau_s = s.get_prop('acq_params')['tau_us']*1e-6
pad_s = s.get_prop('acq_params')['pad_us']*1e-6
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
s.setaxis('tE',tE_axis)
s.setaxis('t2',t2_axis)
fl.next(id_string+'raw data - chunking')
fl.image(s)


# 


print ndshape(s)


# 


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


echo_center = abs(s)['power',-1]['tE',0].argmax('t2').data.item()
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
        niter=10,
        T=1000.
        )
zeroorder_rad, firstorder = sol.x
phshift = exp(-1j*2*pi*f_axis*(firstorder*1e-6))
phshift *= exp(-1j*2*pi*zeroorder_rad)
s *= phshift
print "RELATIVE PHASE SHIFT WAS {:0.1f}\us and {:0.1f}$^\circ$".format(
        firstorder,angle(zeroorder_rad)/pi*180)


# 


checkpoint = s.C


# 


# GO FROM HERE


# 


s = checkpoint.C


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

fl.show();quit()
# 


checkpoint = s.C


# 


# RUN FROM HERE


# 


s = checkpoint.C


# 


fl.next('highest power')
fl.plot(s['power',-1]['nEchoes',0])
fl.plot(s['power',-1]['nEchoes',-1])
fl.next('lowest power')
fl.plot(s['power',2]['nEchoes',0])
fl.plot(s['power',2]['nEchoes',-1])
s.convolve('t2',2)
fl.next('highest power')
fl.plot(s['power',-1]['nEchoes',0])
fl.plot(s['power',-1]['nEchoes',-1])
fl.next('lowest power')
fl.plot(s['power',2]['nEchoes',0])
fl.plot(s['power',2]['nEchoes',-1])


# 


s.reorder('nEchoes',first=False)
fl.next('Echoes at maximum power')
fl.plot(s['power',-1]['t2':(-600,900)],',')


# 


s.reorder('t2',first=False)
s.rename('nEchoes','tE').setaxis('tE',tE_axis)
data = s['t2':(-600,900)].C
fl.next('sliced, after phased - real')
fl.image(data)
fl.next('sliced, after phased - imag')
fl.image(data)


# 


data = data.real.C.sum('t2')


# 


fl.next('plotting first echo')
for x in xrange(shape(s.getaxis('power'))[0]):
    fl.plot(s['tE',0]['power',x]['t2':(-600,900)])


# 


power_list = s.getaxis('power')
print power_list
amplitude_r = empty_like(power_list)
T2_r = empty_like(power_list)


# 


for x in xrange(shape(s.getaxis('power'))[0]):
    print abs(s['tE',0]['power',x].data).max()


# 


for i,k in enumerate(power_list):
    temp = data['power',i].C
    x = tE_axis 
    ydata = temp.data.real
    fl.next('DECAY DATA')
    fl.plot(x,ydata, '.', alpha=0.4, label='%f'%k, human_units=False)
    fitfunc = lambda p, x: p[0]*exp(-x/p[1])
    errfunc = lambda p_arg, x_arg, y_arg: fitfunc(p_arg, x_arg) - y_arg
    p0 = [11102.0,0.6]
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
fl.next('Enhancement vs power: 1.25 mM 4-AT')
fl.plot(corrected_p,'.',human_units=False)
T2_data.set_units('s')
fl.next('T2 vs power: 1.25 mM 4-AT')
fl.plot(T2_data,'.',human_units=False)


fl.show();quit()
