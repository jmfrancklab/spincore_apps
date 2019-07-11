#!/usr/bin/env python
# coding: utf-8

# In[1]:


#%load_ext pyspecdata.ipy
from pyspecdata import *
from scipy.optimize import minimize,basinhopping,nnls
init_logging(level='debug')


# In[2]:


# Initializing dataset


# In[3]:


fl = figlist_var()
date = '190710'
id_string = 'T1CPMG_3'


# In[4]:


filename = date+'_'+id_string+'.h5'
nodename = 'signal'
s = nddata_hdf5(filename+'/'+nodename,
        directory = getDATADIR(
            exp_type = 'test_equip'))

nPoints = s.get_prop('acq_params')['nPoints']
nEchoes = s.get_prop('acq_params')['nEchoes']
nPhaseSteps = s.get_prop('acq_params')['nPhaseSteps']
SW_kHz = s.get_prop('acq_params')['SW_kHz']

s.set_units('t','s')
fl.next('raw data - no clock correction')
fl.image(s)


# In[5]:


clock_corr = True 
if clock_corr:
    s.ft('t',shift=True)
    #clock_correction = 1.479/0.993471 # rad/sec
    #clock_correction = 2.17297/0.982767 # rad/sec
    #clock_correction = 1.04611/3.00005 # rad/sec
    clock_correction = -1.9/6 + 2/1.
    s *= exp(-1j*s.fromaxis('vd')*clock_correction)
    s.ift('t')
    fl.next('raw data - clock correction')
    fl.image(s)


# In[6]:


orig_t = s.getaxis('t')
p90_s = s.get_prop('acq_params')['p90_us']*1e-6
transient_s = s.get_prop('acq_params')['deadtime_us']*1e-6
deblank = 1.0*1e-6
acq_time_s = orig_t[nPoints]
tau_s = s.get_prop('acq_params')['tau_us']*1e-6
pad_s = s.get_prop('acq_params')['pad_us']*1e-6
tE_s = 2.0*p90_s + transient_s + acq_time_s + pad_s
print "ACQUISITION TIME:",acq_time_s,"s"
print "TAU DELAY:",tau_s,"s"
print "TWICE TAU:",2.0*tau_s,"s"
print "ECHO TIME:",tE_s,"s"
vd_list = s.getaxis('vd')
t2_axis = linspace(0,acq_time_s,nPoints)
tE_axis = r_[1:nEchoes+1]*tE_s
s.setaxis('t',None)
s.chunk('t',['ph1','nEchoes','t2'],[nPhaseSteps,nEchoes,-1])
s.setaxis('ph1',r_[0.,2.]/4)
s.setaxis('nEchoes',r_[1:nEchoes+1])
s.setaxis('t2',t2_axis).set_units('t2','s')
s.setaxis('vd',vd_list).set_units('vd','s')
with figlist_var() as fl:
    fl.next('before ph ft')
    fl.image(s)


# In[7]:


print ndshape(s)


# In[8]:


s.ft(['ph1'])
with figlist_var() as fl:
    fl.next(id_string+' image plot coherence')
    fl.image(s)


# In[9]:


s.ft('t2',shift=True)
fl.next(id_string+' image plot coherence -- ft')
fl.image(s)


# In[10]:


s.ift('t2')
s.reorder('vd',first=False)
coh = s.C.smoosh(['ph1','nEchoes','t2'],'t2').reorder('t2',first=False)
coh.setaxis('t2',orig_t).set_units('t2','s')
s = s['ph1',1].C


# In[11]:


with figlist_var() as fl:
    s.ft('t2')
    fl.next('plotting f')
    fl.plot(s['nEchoes',0]['vd',0])
    s.ift('t2')
    fl.next('plotting t')
    fl.plot(s['nEchoes',0]['vd',0])


# In[12]:


s.reorder('vd',first=True)
echo_center = abs(s)['nEchoes',0]['vd',0].argmax('t2').data.item()
s.setaxis('t2', lambda x: x-echo_center)
with figlist_var() as fl:
    fl.next('check center')
    fl.image(s)


# In[13]:


with figlist_var() as fl:
    fl.next('plotting t')
    fl.plot(s['nEchoes',0]['vd',0])
    s.ft('t2')
    fl.next('plotting f')
    fl.plot(s['nEchoes',0]['vd',0])
    s.ift('t2')


# In[14]:


s.ft('t2')
fl.next('before phased - real ft')
fl.image(s.real)
fl.next('before phased - imag ft')
fl.image(s.imag)
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
        niter=200,
        T=1000.
        )
zeroorder_rad, firstorder = sol.x
phshift = exp(-1j*2*pi*f_axis*(firstorder*1e-6))
phshift *= exp(-1j*2*pi*zeroorder_rad)
s *= phshift
print "RELATIVE PHASE SHIFT WAS {:0.1f}\us and {:0.1f}$^\circ$".format(
        firstorder,angle(zeroorder_rad)/pi*180)
if s['nEchoes',0].data[:].sum().real < 0:
    s *= -1
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
fl.show()


# In[15]:


# CHECKPOINT


# In[16]:


checkpoint = s.C


# In[ ]:


# IF WANTING TO FIND T2 DECAY


# In[17]:


T2_fits = True
if T2_fits:
    data_T2 = checkpoint.C
    data_T2.rename('nEchoes','tE').setaxis('tE',tE_axis)
    for index in r_[0:len(vd_list):1]:
        temp = data_T2['vd',index].C.sum('t2')
        #fl.next('Fit decay')
        x = tE_axis 
        ydata = temp.data.real
        if ydata.sum() < 0:
            ydata *= -1
        ydata /= max(ydata)
        #fl.plot(x,ydata, '.', alpha=0.4, label='data %d'%index, human_units=False)
        fitfunc = lambda p, x: exp(-x/p[0])
        errfunc = lambda p_arg, x_arg, y_arg: fitfunc(p_arg, x_arg) - y_arg
        p0 = [0.2]
        p1, success = leastsq(errfunc, p0[:], args=(x, ydata))
        x_fit = linspace(x.min(),x.max(),5000)
        #fl.plot(x_fit, fitfunc(p1, x_fit),':', label='fit %d (T2 = %0.2f ms)'%(index,p1[0]*1e3), human_units=False)
        fl.next('T2 Decay: Fit')
        fl.plot(x_fit, fitfunc(p1, x_fit),':', label='fit %d (T2 = %0.2f ms)'%(index,p1[0]*1e3), human_units=False)
        xlabel('t (sec)')
        ylabel('Intensity')
        T2 = p1[0]
        print "T2:",T2,"s"


# CHECKPOINT

# In[18]:


d = checkpoint.C
d = d.C.sum('t2')
d = d.real


# In[36]:


print "Constructing kernels..."
Nx = 100
Ny = 100
Nx_ax = nddata(logspace(-3,1,Nx),'T1')
Ny_ax = nddata(logspace(-3,1,Ny),'T2')
data = d.C
data.rename('vd','tau1').setaxis('tau1',vd_list)
data.rename('nEchoes','tau2').setaxis('tau2',tE_axis)


# In[51]:


this = lambda x1,x2,y1,y2: (1-2*exp(-x1/y1),exp(-x2/y2))

x = data.C.nnls(('tau1','tau2'),
       (Nx_ax,Ny_ax),
       (lambda x1,x2: 1.-2*exp(-x1/x2),
        lambda y1,y2: exp(-y1/y2)),
                 l='BRD')

x.setaxis('T1',log10(Nx_ax.data)).set_units('T1',None)
x.setaxis('T2',log10(Ny_ax.data)).set_units('T2',None)


# In[52]:


image(x)
xlabel(r'$log(T_2/$s$)$')
ylabel(r'$log(T_1/$s$)$')
title('Higher SNR, repeat July 9, 2019 T1-T2 measurement')


# In[53]:


print ndshape(x)


# In[76]:


image(x)
xlabel(r'$log(T_2/$s$)$')
ylabel(r'$log(T_1/$s$)$')
title('Higher SNR, repeat July 9, 2019 T1-T2 measurement')
fit = x.C.get_prop('K1').dot(x.C.dot(x.C.get_prop('K2')))
residual  = data - fit
figure(figsize=(13,8));suptitle('DATASET: %s_%s'%(date,id_string))
subplot(221);subplot(221).set_title('DATA\n $ m $')
image(data)
subplot(222);subplot(222).set_title('FIT\n $K_{1}$ $f$ $K_{2}$')
image(fit)
subplots_adjust(hspace=0.5)
subplot(223);subplot(223).set_title('DATA - FIT\n $ m $ - $K_{1}$ $f$ $K_{2}$')
image(residual)
subplot(224);subplot(224).set_title('|DATA - FIT|\n |$ m $ - $K_{1}$ $f$ $K_{2}$|')
image(abs(residual))


# In[60]:


x_test = x.C
x_test['T1':(None,-0.5)] = 0
x_test['T2':(-0.9,None)] = 0


# In[77]:


title('Only cross peak')
image(x_test)
xlabel(r'$log(T_2/$s$)$')
ylabel(r'$log(T_1/$s$)$')
fit = x.C.get_prop('K1').dot(x_test.C.dot(x.C.get_prop('K2')))
residual  = data - fit
figure(figsize=(13,8));suptitle('DATASET: ONLY CROSSPEAK, %s_%s'%(date,id_string))
subplot(221);subplot(221).set_title('DATA\n $ m $')
image(data)
subplot(222);subplot(222).set_title('FIT\n $K_{1}$ $f$ $K_{2}$')
image(fit)
subplots_adjust(hspace=0.5)
subplot(223);subplot(223).set_title('DATA - FIT\n $ m $ - $K_{1}$ $f$ $K_{2}$')
image(residual)
subplot(224);subplot(224).set_title('|DATA - FIT|\n |$ m $ - $K_{1}$ $f$ $K_{2}$|')
image(abs(residual))


# In[81]:


x_test2 = x.C
x_test2['T1':(-0.5,None)] = 0
x_test2['T2':(-1,None)] = 0
title('Bottom left peak')
image(x_test2)
xlabel(r'$log(T_2/$s$)$')
ylabel(r'$log(T_1/$s$)$')
fit = x.C.get_prop('K1').dot(x_test2.C.dot(x.C.get_prop('K2')))
residual  = data - fit
figure(figsize=(13,8));suptitle('DATASET: BOTTOM LEFT PEAK, %s_%s'%(date,id_string))
subplot(221);subplot(221).set_title('DATA\n $ m $')
image(data)
subplot(222);subplot(222).set_title('FIT\n $K_{1}$ $f$ $K_{2}$')
image(fit)
subplots_adjust(hspace=0.5)
subplot(223);subplot(223).set_title('DATA - FIT\n $ m $ - $K_{1}$ $f$ $K_{2}$')
image(residual)
subplot(224);subplot(224).set_title('|DATA - FIT|\n |$ m $ - $K_{1}$ $f$ $K_{2}$|')
image(abs(residual))


# In[80]:


x_test3 = x.C
#x_test3['T1':(None,-1)] = 0
x_test3['T2':(None,-1)] = 0
title('Upper right peak')
image(x_test3)
fit = x.C.get_prop('K1').dot(x_test3.C.dot(x.C.get_prop('K2')))
residual  = data - fit
figure(figsize=(13,8));suptitle('DATASET: UPPER RIGHT PEAK, %s_%s'%(date,id_string))
subplot(221);subplot(221).set_title('DATA\n $ m $')
image(data)
subplot(222);subplot(222).set_title('FIT\n $K_{1}$ $f$ $K_{2}$')
image(fit)
subplots_adjust(hspace=0.5)
subplot(223);subplot(223).set_title('DATA - FIT\n $ m $ - $K_{1}$ $f$ $K_{2}$')
image(residual)
subplot(224);subplot(224).set_title('|DATA - FIT|\n |$ m $ - $K_{1}$ $f$ $K_{2}$|')
image(abs(residual))


# In[ ]:




