from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping,nnls
fl = figlist_var()
rcParams['figure.figsize'] = [10,6]
for date,id_string in [
    ('191107','echo_DNP'),
    ('191107','echo_DNP_2'),
        ]:
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    nPoints = s.get_prop('acq_params')['nPoints']
    SW_kHz = s.get_prop('acq_params')['SW_kHz']
    nPhaseSteps = s.get_prop('acq_params')['nPhaseSteps']
    s.set_units('t','s')
    print s.get_prop('meter_powers')
    print ndshape(s)
    fl.next(id_string+'raw data ')
    fl.image(s)
    orig_t = s.getaxis('t')
    acq_time_s = orig_t[nPoints]
    t2_axis = orig_t[nPoints]
    s.setaxis('t',None)
    s.reorder('t',first=True)
    s.chunk('t',['ph2','ph1','t2'],[2,4,-1])
    s.setaxis('ph2',r_[0.,2.]/4)
    s.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    s.setaxis('t2',t2_axis)
    s.reorder('t2',first=False)
    s.ft('t2',shift=True)
    s.ft(['ph1','ph2'])
    fl.next('raw data')
    fl.image(s)
    s = s['ph1',1]['ph2',0].C
    s.reorder('t2',first=True)
    s.ift('t2')
    fl.next('signal, time domain')
    fl.plot(s)
    t2_max = zeros_like(s.getaxis('power'))
    for x in xrange(len(s.getaxis('power'))):
        t2_max[x] = abs(s['power',x]).argmax('t2',raw_index=True).data
    s.setaxis('t2',lambda t: t - s.getaxis('t2')[int(t2_max.mean())])
    fl.next('signal, time domain shifted')
    fl.plot(s)
    s = s['t2':(0,None)]
    s['t2',0] *= 0.5
    fl.next('signal, time domain shifted+sliced')
    fl.plot(s)
    fl.next('signal, freq post-proc')
    fl.plot(s.C.ft('t2'))
    # Because the phasing causes us to lose the sign
    remember_sign = zeros_like(s.getaxis('power'))
    for x in xrange(len(s.getaxis('power'))):
        if s['power',x].data.real.sum() > 0:
            remember_sign[x] = 1.0
        else:
            remember_sign[x] = -1.0
    # Preliminary phasing procedure
    s.ft('t2')
    ##for x in xrange(len(s.getaxis('power'))):
    ##    temp = s['power',x].C
    ##    fl.next('power %f'%s.getaxis('power')[x])
    ##    fl.plot(temp,label='before')
    ##    SW = diff(temp.getaxis('t2')[r_[0,-1]]).item()
    ##    thisph1 = nddata(r_[-6:6:2048j]/SW,'phi1').set_units('phi1','s')
    ##    phase_test_r = temp * exp(-1j*2*pi*thisph1*temp.fromaxis('t2'))
    ##    phase_test_rph0 = phase_test_r.C.sum('t2')
    ##    phase_test_rph0 /= abs(phase_test_rph0)
    ##    phase_test_r /= phase_test_rph0
    ##    cost = abs(phase_test_r.real).sum('t2')
    ##    ph1_opt = cost.argmin('phi1').data
    ##    temp *= exp(-1j*2*pi*ph1_opt*temp.fromaxis('t2'))
    ##    ph0 = temp.C.sum('t2')
    ##    ph0 /= abs(ph0)
    ##    temp /= ph0
    ##    fl.next('power %f'%s.getaxis('power')[x])
    ##    fl.plot(temp,label='after')
    ##    s['power',x] *= exp(-1j*2*pi*ph1_opt*s.fromaxis('t2'))
    ##    s['power',x] /= ph0
    # # Check prelim phasing
    #{{{ I don't know what the following block of code was doing?
    #f_max = zeros_like(s.getaxis('power'))
    #for x in xrange(len(s.getaxis('power'))):
    #    f_max[x] = s.getaxis('t2')[s['power',x].data.argmax()]
    #s.setaxis('t2',lambda t: t - f_max.mean())
    #fl.next('freq, shifted')
    #fl.plot(s['t2':(-300,300)]*remember_sign)
    #}}}
    # # Enhancement curve with prelim phasing
    enhancement = s['t2':(-1e3,1e3)].C
    fl.next('Check slice')
    fl.plot(enhancement.C)
    enhancement.sum('t2').real
    #enhancement *= remember_sign
    enhanced = enhancement.data[1:]
    enhanced /= max(enhanced)
    #enhancement.setaxis('power',s.get_prop('meter_powers'))
    fl.next('150uL TEMPOL enhancement curve')
    power_axis_dBm = array(s.get_prop('meter_powers'))
    power_axis_W = zeros_like(power_axis_dBm)
    power_axis_W[:] = (1e-2*10**((power_axis_dBm[:]+10.)*1e-1))
    fl.plot(power_axis_W,enhanced,'.')
xlabel('power meter reading (W)')
ylabel('enhancement')
save_fig = False
if save_fig:
    savefig('191107_TEMPOL.png',
            transparent=True,
            bbox_inches='tight',
            pad_inches=0)
fl.show();quit()

# # Beginning Hermitian symmetry phasing procedure

# In[ ]:


abs(temp.getaxis('t2')).min()


# In[ ]:


temp = s['power',-1].C

df = diff(temp.getaxis('t2')[r_[0,1]])[0]
max_hwidth = 10
window_hwidth = 5
max_shift = (max_hwidth - window_hwidth)*df
center_index = where(abs(temp.getaxis('t2'))==abs(temp.getaxis('t2')).min())[0][0]
temp_slice = temp['t2',center_index - max_hwidth : center_index + max_hwidth+1].C
sliced_center_index = where(abs(temp_slice.getaxis('t2'))==abs(temp_slice.getaxis('t2')).min())[0][0]
f_axis = temp_slice.fromaxis('t2')

def hermitian_costfun(p):
    zerorder_rad,firstorder = p
    phshift = exp(-1j*2*pi*f_axis*(firstorder*1e-6))
    phshift *= exp(-1j*2*pi*zerorder_rad)
    temp = phshift * temp_slice
    deviation = temp['t2',sliced_center_index - window_hwidth : sliced_center_index + window_hwidth+1].C
    deviation -= deviation['t2',::-1].C.run(conj)
    #deviation -= deviation['power',-1]['t2',::-1].C.run(conj)
    return (abs(deviation.data)**2)[:].sum()

iteration = 0

def print_func(x,f,accepted):
    global iteration
    print(iteration, x, f, int(accepted))
    iteration = iteration+1

sol = basinhopping(hermitian_costfun, r_[0.,0.],
                  minimizer_kwargs={"method":'L-BFGS-B'},
                  callback=print_func,
                  stepsize=100.,
                  niter=10,
                  T=1000.
                  )
zerorder_rad,firstorder = sol.x

f_axis = temp.getaxis('t2')

phshift = exp(-1j*2*pi*f_axis*(firstorder*1e-6))
phshift *= exp(-1j*2*pi*zerorder_rad)

temp *= phshift

with figlist_var() as fl:
    fl.next('frequency, phased')
    fl.plot(temp)


# # Preparing Hermitian symm phased data for enhancement curve

# In[ ]:


after = s.C


# In[ ]:


after *= phshift
after *= remember_sign


# In[ ]:


before = s.C
before *= remember_sign


# In[ ]:


with figlist_var() as fl:
    
    fl.next('before Hermitian symm phasing')
    fl.plot(before.real['t2':(-300,300)])
    fl.next('after Hermitian symm phasing')
    fl.plot(after.real['t2':(-300,300)])


# In[ ]:


test = after['t2':(-300,300)].C


# In[ ]:


test.sum('t2').real


# # Plotting enhancement curves for both

# In[ ]:


with figlist_var() as fl:
    fl.next('enhancement, programmed power')
    fl.plot(enhancement/enhancement['power',0].data,'.',alpha=0.7,label='Preliminary phasing')
    fl.plot(test/test['power',0].data,'.',alpha=0.7,label='After Hermitian symm phasing')
    legend()
    savefig('20190814_enhancement_prog_power_phase_error.pdf',
            transparent=True,
            bbox_inches='tight',
             pad_inches=0)


# # Using new power axis

# In[ ]:


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


# In[ ]:


tx_mon = r_[0.0,
            1.66e-3,
            1.66e-3,
           1.66e-3,
           3.33e-3,
           5.00e-3,
           6.66e-3,
           15.0e-3,
           15.0e-3,
           201e-3,
           231e-3,
           311e-3,
           411e-3,
           411e-3,
           470e-3,
           470e-3,
           470e-3,
           470e-3,
           540e-3,
           616e-3,
           616e-3,
           696e-3,
           696e-3]
tx_mon_corr = zeros_like(tx_mon)
for x in xrange(len(tx_mon)):
    tx_mon_corr[x] = 1e-3*10**((convert_to_power(tx_mon[x],'Tx')+29)/10.)


# In[ ]:


tx_mon_power_list = tx_mon_corr*1e3
tx_enhancement = enhancement.C
tx_enhancement.setaxis('power',tx_mon_power_list)
tx_test = test.C
tx_test.setaxis('power',tx_mon_power_list)


# In[ ]:


with figlist_var() as fl:
    fl.next('enhancement, TX_MON power axis')
    fl.plot(tx_enhancement/tx_enhancement['power',0].data,'.',alpha=0.7,label='Preliminary phasing')
    fl.plot(tx_test/tx_test['power',0].data,'.',alpha=0.7,label='After Hermitian symm phasing')
    legend()
    #xlim(0.0,0.2)
    savefig('20190814_enhancement_txmon_phase_error.pdf',
            transparent=True,
            bbox_inches='tight',
             pad_inches=0)


# In[ ]:


print ndshape(after)


# In[ ]:


with figlist_var() as fl:
    fl.next('signal after Hermitian symmetry phasing and manual 0th order adjustment')
    fl.plot(after*exp(1j*0.2*pi))
    savefig('20190814_spectra_phase_fixed.pdf',
        transparent=True,
        bbox_inches='tight',
         pad_inches=0)


# In[ ]:


test = after.C*exp(1j*0.2*pi)
test = test['t2':(-200,250)]


# In[ ]:


with figlist_var() as fl:
    fl.next('signal')
    fl.plot(test)


# In[ ]:


test.sum('t2').real


# In[ ]:


with figlist_var() as fl:
    fl.next('enhancement, programmed power axis, manual phasing')
    #fl.plot(enhancement/enhancement['power',0].data,'.',alpha=0.7,label='Preliminary phasing')
    fl.plot(test/test['power',0].data,'.',alpha=0.7)#,label='After Hermitian symm phasing')
    #legend()
    savefig('20190814_enhancement_prog_power_manual_phasing.pdf',
           transparent=True,
            bbox_inches='tight',
             pad_inches=0)


# In[ ]:


tx_test = test.C
tx_test.setaxis('power',tx_mon_power_list)


# In[ ]:


with figlist_var() as fl:
    fl.next('enhancement, TX_MON power axis, manual phasing')
    #fl.plot(tx_enhancement/tx_enhancement['power',0].data,'.',alpha=0.7)#,label='Preliminary phasing')
    fl.plot(tx_test/tx_test['power',0].data,'.',alpha=0.7)#,label='After Hermitian symm phasing')
    #legend()
    #xlim(0.0,0.2)
    savefig('20190814_enhancement_txmon_power_manula_phasing.pdf',
            transparent=True,
            bbox_inches='tight',
             pad_inches=0)

