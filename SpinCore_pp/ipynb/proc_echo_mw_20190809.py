
# coding: utf-8

# In[ ]:


from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping,nnls
fl = figlist_var()
rcParams['figure.figsize'] = [10,6]


# In[ ]:


date,id_string = '190805','echo_DNP'


# In[ ]:


filename = date+'_'+id_string+'.h5'
nodename = 'signal'
s = nddata_hdf5(filename+'/'+nodename,
        directory = getDATADIR(
            exp_type = 'test_equip'))
#nPoints = s.get_prop('acq_params')['nPoints']
nPoints = 128
SW_kHz = s.get_prop('acq_params')['SW_kHz']
nPhaseSteps = s.get_prop('acq_params')['nPhaseSteps']
s.set_units('t','s')
print ndshape(s)


# In[ ]:


with figlist_var() as fl:
    fl.next(id_string+'raw data ')
    fl.image(s)


# In[ ]:


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
with figlist_var() as fl:
    fl.next('raw data')
    fl.image(s)


# In[ ]:


s = s['ph1',1]['ph2',0].C


# In[ ]:


checkpoint = s.C


# # RUN FROM HERE

# In[ ]:


s = checkpoint.C


# In[ ]:


s.reorder('t2',first=True)
s.ift('t2')
with figlist_var() as fl:
    fl.next('plotting checkpoint data')
    fl.plot(s)


# In[ ]:


t2_max = zeros_like(s.getaxis('power'))
for x in xrange(len(s.getaxis('power'))):
    t2_max[x] = abs(s['power',x]).argmax('t2',raw_index=True).data
s.setaxis('t2',lambda t: t - s.getaxis('t2')[int(t2_max.mean())])
with figlist_var() as fl:
    fl.next('shifted')
    fl.plot(s)


# In[ ]:


s = s['t2':(0,None)]
s['t2',0] *= 0.5
with figlist_var() as fl:
    fl.next('sliced')
    fl.plot(s)
    fl.next('ftd')
    fl.plot(s.C.ft('t2'))


# # Because the phasing causes us to lose the sign

# In[ ]:


remember_sign = zeros_like(s.getaxis('power'))
for x in xrange(len(s.getaxis('power'))):
    if s['power',x].data.real.sum() > 0:
        remember_sign[x] = 1.0
    else:
        remember_sign[x] = -1.0


# # Preliminary phasing procedure

# In[ ]:


s.ft('t2')


# In[ ]:


for x in xrange(len(s.getaxis('power'))):
    temp = s['power',x].C
    fl.next('power %f'%s.getaxis('power')[x])
    fl.plot(temp,label='before')
    SW = diff(temp.getaxis('t2')[r_[0,-1]]).item()
    thisph1 = nddata(r_[-6:6:2048j]/SW,'phi1').set_units('phi1','s')
    phase_test_r = temp * exp(-1j*2*pi*thisph1*temp.fromaxis('t2'))
    phase_test_rph0 = phase_test_r.C.sum('t2')
    phase_test_rph0 /= abs(phase_test_rph0)
    phase_test_r /= phase_test_rph0
    cost = abs(phase_test_r.real).sum('t2')
    ph1_opt = cost.argmin('phi1').data
    temp *= exp(-1j*2*pi*ph1_opt*temp.fromaxis('t2'))
    ph0 = temp.C.sum('t2')
    ph0 /= abs(ph0)
    temp /= ph0
    fl.next('power %f'%s.getaxis('power')[x])
    fl.plot(temp,label='after')
    s['power',x] *= exp(-1j*2*pi*ph1_opt*s.fromaxis('t2'))
    s['power',x] /= ph0


# # Check prelim phasing

# In[ ]:


f_max = zeros_like(s.getaxis('power'))
for x in xrange(len(s.getaxis('power'))):
    f_max[x] = s.getaxis('t2')[s['power',x].data.argmax()]
s.setaxis('t2',lambda t: t - f_max.mean())
with figlist_var() as fl:
    fl.next('shifted')
    fl.plot(s['t2':(-300,300)])


# # Enhancement curve with prelim phasing

# In[ ]:


enhancement = s['t2':(-300,300)].C
enhancement.sum('t2').real
enhancement *= remember_sign
with figlist_var() as fl:
    fl.next('Prelim phasing enhancement')
    fl.plot(enhancement,'.')


# # Beginning Hermitian symmetry phasing procedure

# In[ ]:


temp = s['power',-1].C

df = diff(temp.getaxis('t2')[r_[0,1]])[0]
max_hwidth = 10
window_hwidth = 5
max_shift = (max_hwidth - window_hwidth)*df
center_index = where(temp.getaxis('t2')==abs(temp.getaxis('t2')).min())[0][0]
temp_slice = temp['t2',center_index - max_hwidth : center_index + max_hwidth+1].C
sliced_center_index = where(temp_slice.getaxis('t2')==abs(temp_slice.getaxis('t2')).min())[0][0]
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
                  niter=100,
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


test = s.C


# In[ ]:


test *= phshift


# In[ ]:


test *= remember_sign


# In[ ]:


test = test['t2':(-300,300)].C


# In[ ]:


test.sum('t2').real


# # Plotting enhancement curves for both

# In[ ]:


with figlist_var() as fl:
    fl.next('enhancement')
    fl.plot(enhancement/enhancement['power',0].data,'.',alpha=0.7,label='Preliminary phasing')
    fl.plot(test/test['power',0].data,'.',alpha=0.7,label='After Hermitian symm phasing')
    legend()
    savefig('20190809_enhancement.pdf',
            transparent=True,
            bbox_inches='tight',
             pad_inches=0)

