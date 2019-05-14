
# coding: utf-8

# In[1]:


from pyspecdata import *
from scipy.linalg import expm


# In[2]:


#omega1 = 30e3 # 5kHZ times 2pi
omega1 = 30e3*2*pi


# In[3]:


def gamma_imp(T1,T2,offset,omega1,phase):
    return array([ [0,0,0,0]
                  ,[0,1./T2,offset,-omega1*sin(phase)]
                  ,[0,-offset,1./T2,omega1*cos(phase)]
                  ,[-1./T1,omega1*sin(phase),-omega1*cos(phase),1./T1]
                 ], dtype=double)


# In[4]:


Liou_vec = array([[1],[0],[0],[1]], dtype=double)


# In[5]:


T1 = 0.8
T2 = 0.3
offset = 0.0
phase = 0.0


# In[10]:


time_len = 1000
dt = 4e-3
t2_axis = r_[0:time_len]*dt

fid = ndshape([len(t2_axis)],['t2']).alloc()
fid.setaxis('t2',t2_axis)
fid.set_units('t2','s')

input_vec = expm(-50e-6*gamma_imp(T1,T2,offset,omega1,0.0)).dot(Liou_vec)
U_dt = expm(-dt*gamma_imp(T1,T2,offset,0.0,0.0)) 
last_rho = input_vec.copy()
for j,t_point in enumerate(t2_axis):
    s_x,s_y = last_rho[r_[1,2]]
    fid['t2',j] = (s_x) - 1j*(s_y)
    last_rho = U_dt.dot(last_rho)
with figlist_var() as fl:
    fl.next('time domain')
    fl.plot(fid.real)
    fl.plot(fid.imag)


# In[11]:


time_len = 1000
dt = 4e-3
t2_axis = r_[0:time_len]*dt

fid = ndshape([len(t2_axis)],['t2']).alloc()
fid.setaxis('t2',t2_axis)
fid.set_units('t2','s')
input_vec = expm(-50e-6*gamma_imp(T1,T2,offset,omega1,0.0)).dot(Liou_vec)
for j,t_point in enumerate(t2_axis):
    U = expm(-t_point*gamma_imp(T1,T2,offset,0,0))
    fid['t2',j] = U.dot(input_vec)[1]-1j*U.dot(input_vec)[2]

with figlist_var() as fl:
    fl.next('time domain')
    fl.plot(fid.real)
    fl.plot(fid.imag)


# # NUTATION CURVE

# In[12]:


2*pi/omega1/4


# In[19]:


time_len = 1000
dt = 4e-3
t2_axis = r_[0:time_len]*dt

pulse_list = linspace(1e-6,40e-6,50)

fid = ndshape([len(pulse_list),len(t2_axis)],['p','t2']).alloc()
fid.setaxis('p',pulse_list)
fid.setaxis('t2',t2_axis)
fid.set_units('p','s')
fid.set_units('t2','s')
for i,p_val in enumerate(pulse_list):
    input_vec = expm(-p_val*gamma_imp(T1,T2,offset,omega1,0.0)).dot(Liou_vec)
    for j,t_point in enumerate(t2_axis):
        U = expm(-t_point*gamma_imp(T1,T2,offset,0,0))
        fid['p',i]['t2',j] = U.dot(input_vec)[1]-1j*U.dot(input_vec)[2]
        


# In[21]:


with figlist_var() as fl:
    fl.next('pulse length')
    fl.image(fid)
    ylim(15,20)


# # SIMPLE 90 (On resonance)

# In[30]:


p90 = 2*pi/omega1/4


# In[31]:


time_len = 1000
dt = 4e-3
t2_axis = r_[0:time_len]*dt

T1 = 0.8
T2 = 0.3

fid = ndshape([len(t2_axis)],['t2']).alloc()
fid.setaxis('t2',t2_axis)
fid.set_units('t2','s')
input_vec = expm(-p90*gamma_imp(T1,T2,offset,omega1,0.0)).dot(Liou_vec)
for j,t_point in enumerate(t2_axis):
    U = expm(-t_point*gamma_imp(T1,T2,offset,0,0))
    fid['t2',j] = U.dot(input_vec)[1]-1j*U.dot(input_vec)[2]

with figlist_var() as fl:
    fl.next('time domain')
    fl.plot(fid.real)
    fl.plot(fid.imag)


# # SIMPLE 90 (With offset)

# In[32]:


time_len = 1000
dt = 4e-3
t2_axis = r_[0:time_len]*dt

T1 = 0.8
T2 = 0.3
offset = 3*2*pi

fid = ndshape([len(t2_axis)],['t2']).alloc()
fid.setaxis('t2',t2_axis)
fid.set_units('t2','s')
input_vec = expm(-p90*gamma_imp(T1,T2,offset,omega1,0.0)).dot(Liou_vec)
for j,t_point in enumerate(t2_axis):
    U = expm(-t_point*gamma_imp(T1,T2,offset,0,0))
    fid['t2',j] = U.dot(input_vec)[1]-1j*U.dot(input_vec)[2]

with figlist_var() as fl:
    fl.next('time domain')
    fl.plot(fid.real)
    fl.plot(fid.imag)


# # SIMPLE 180

# In[33]:


time_len = 1000
dt = 4e-3
t2_axis = r_[0:time_len]*dt

T1 = 0.8
T2 = 0.3

fid = ndshape([len(t2_axis)],['t2']).alloc()
fid.setaxis('t2',t2_axis)
fid.set_units('t2','s')
input_vec = expm(-2*p90*gamma_imp(T1,T2,offset,omega1,0.0)).dot(Liou_vec)
for j,t_point in enumerate(t2_axis):
    U = expm(-t_point*gamma_imp(T1,T2,offset,0,0))
    fid['t2',j] = U.dot(input_vec)[1]-1j*U.dot(input_vec)[2]
with figlist_var() as fl:
    fl.next('time domain')
    fl.plot(fid.real)
    fl.plot(fid.imag)


# # INVERSION RECOVERY

# In[36]:


vd_list = [1e-3,1e-2,0.1,0.4,0.55,0.7,0.9,1.2,1.5]

time_len = 1000
dt = 4e-3
t2_axis = r_[0:time_len]*dt

T1 = 0.8
T2 = 0.3
offset = 3*2*pi

fid = ndshape([len(vd_list),len(t2_axis)],['vd','t2']).alloc()
fid.setaxis('t2',t2_axis)
fid.setaxis('vd',vd_list)
fid.set_units('t2','s')
fid.set_units('vd','s')

for i,vd_val in enumerate(vd_list):
    input_vec = expm(-p90*gamma_imp(T1,T2,offset,omega1,0.0)
                    ).dot(expm(-vd_val*gamma_imp(T1,T2,offset,0.0,0.0)
                    ).dot(expm(-2*p90*gamma_imp(T1,T2,offset,omega1,0.0)
                    ).dot(Liou_vec)))
    for j,t_point in enumerate(t2_axis):
        U = expm(-t_point*gamma_imp(T1,T2,offset,0,0))
        fid['vd',i]['t2',j] = U.dot(input_vec)[1]-1j*U.dot(input_vec)[2]


# In[37]:


with figlist_var() as fl:
    fl.next('time domain')
    fl.image(fid)


# In[38]:


fid.ft('t2',shift=True)
with figlist_var() as fl:
    fl.next('f domain')
    fl.image(fid['t2':(-2.5,2.5)])


# # ECHO

# In[ ]:


# Echo code that JF wrote
p90 = 2*pi/omega1/4.
time_len = 1000
dt = 1e-3
t2_axis = r_[0:time_len]*dt

T1 = 0.8
T2 = 0.3

fid = ndshape([len(offset_axis),len(t2_axis)],['Omega','t2']).alloc()
fid.setaxis('t2',t2_axis)
fid.setaxis('Omega',offset_axis)
fid.set_units('t2','s')

for i,offset_pt in enumerate(offset_axis):
    offset = offset_pt*2*pi
    offset_w = (1./(sigma*sqrt(2*pi)))*exp(-0.5*((offset_pt-mu)/sigma)**2)
    U_90 = expm(-p90*gamma_imp(T1,T2,offset,omega1,0.0))
    U_dt = expm(-dt*gamma_imp(T1,T2,offset,0,0))
    input_vec = U_90.dot(Liou_vec.ravel()*r_[1,1,1,offset_w])
    input_vec = matrix_power(U_dt,400).dot(input_vec) # interpulse delay
    input_vec = U_90.dot(U_90).dot(input_vec) # 180 pulse
    last_rho = input_vec.copy()
    for j,t_point in enumerate(t2_axis):
        fid['Omega',i]['t2',j] = (r_[1,-1j]*last_rho[r_[1,2]]).sum()
        last_rho = U_dt.dot(last_rho)
with figlist_var() as fl:
    fl.next('single isochromat')
    s_single = fid['Omega',ndshape(fid)['Omega']//2]
    fl.plot(s_single.real)
    fl.plot(s_single.imag)
    fl.next('echo?')
    fid.sum('Omega')
    fl.plot(fid.real)
    fl.plot(fid.imag)


# In[87]:


# Generating offset of gradients for echo
mu = -10
sigma = 5
offset_axis = linspace(-15,-5,25)
offset_list = empty_like(offset_axis)
for i,offset_pt in enumerate(offset_axis):
    offset = (1./(sigma*sqrt(2*pi)))*exp(-0.5*((offset_pt-mu)/sigma)**2)
    offset_list[i] = offset
center = offset_axis[12]


# In[90]:


# Simple 90 with gradient of offsets (Gaussian distribution)
time_len = 1000
dt = 1.5e-3
t2_axis = r_[0:time_len]*dt

T1 = 0.8
T2 = 0.3

fid = ndshape([len(offset_axis),len(t2_axis)],['Omega','t2']).alloc()
fid.setaxis('t2',t2_axis)
fid.setaxis('Omega',offset_axis)
fid.set_units('t2','s')

for i,offset_pt in enumerate(offset_axis):
    offset = offset_pt*2*pi
    offset_w = (1./(sigma*sqrt(2*pi)))*exp(-0.5*((offset_pt-mu)/sigma)**2)
    U_90 = expm(-p90*gamma_imp(T1,T2,offset,omega1,0.0))
    input_vec = U_90.dot(Liou_vec)
    for j,t_point in enumerate(t2_axis):
        U = expm(-t_point*gamma_imp(T1,T2,offset,0,0))
        fid['Omega',i]['t2',j] = U.dot(input_vec)[1]-1j*U.dot(input_vec)[2]


# In[91]:


with figlist_var() as fl:
    fl.next('single isochromat')
    s_single = fid['Omega',ndshape(fid)['Omega']//2]
    fl.plot(s_single.real)
    fl.plot(s_single.imag)
    fl.next('With inhomogenenous B0')
    fid.sum('Omega')
    fl.plot(fid.real)
    fl.plot(fid.imag)


# In[97]:


# Next trying to find/see an echo
time_len = 1000
dt = 1.5e-3
t2_axis = r_[0:time_len]*dt

T1 = 0.8
T2 = 0.3
delay = 0.8
pts_delay = delay/dt

fid = ndshape([len(offset_axis),len(t2_axis)],['Omega','t2']).alloc()
fid.setaxis('t2',t2_axis)
fid.setaxis('Omega',offset_axis)
fid.set_units('t2','s')

for i,offset_pt in enumerate(offset_axis):
    offset = offset_pt*2*pi
    offset_w = (1./(sigma*sqrt(2*pi)))*exp(-0.5*((offset_pt-mu)/sigma)**2)
    U_90 = expm(-p90*gamma_imp(T1,T2,offset,omega1,0.0))
    U_dt = expm(-dt*gamma_imp(T1,T2,offset,0,0))
    input_vec = U_90.dot(Liou_vec.ravel()*r_[1,1,1,offset_w])
    input_vec = matrix_power(U_dt,int(pts_delay)).dot(input_vec) # interpulse delay
    input_vec = U_90.dot(U_90).dot(input_vec) # 180 pulse
    for j,t_point in enumerate(t2_axis):
        U = expm(-t_point*gamma_imp(T1,T2,offset,0,0))
        fid['Omega',i]['t2',j] = U.dot(input_vec)[1]-1j*U.dot(input_vec)[2]


# In[98]:


with figlist_var() as fl:
    fl.next('single isochromat')
    s_single = fid['Omega',ndshape(fid)['Omega']//2]
    fl.plot(s_single.real)
    fl.plot(s_single.imag)
    fl.next('With inhomogenenous B0')
    fid.sum('Omega')
    fl.plot(fid.real)
    fl.plot(fid.imag)


# # CPMG

# In[104]:


# Next trying to find/see an echo
time_len = 1000
dt = 1.5e-3
t2_axis = r_[0:time_len]*dt

T1 = 0.8
T2 = 0.3
delay = 0.2
pts_delay = delay/dt

n_echoes = 4.0

fid = ndshape([len(n_echoes),len(offset_axis),len(t2_axis)],['Echoes','Omega','t2']).alloc()
fid.setaxis('t2',t2_axis)
fid.setaxis('Omega',offset_axis)
fid.setaxis('n_echoes',r_[0:n_echoes]+1)
fid.set_units('t2','s')

for i,offset_pt in enumerate(offset_axis):
    offset = offset_pt*2*pi
    offset_w = (1./(sigma*sqrt(2*pi)))*exp(-0.5*((offset_pt-mu)/sigma)**2)
    U_90 = expm(-p90*gamma_imp(T1,T2,offset,omega1,0.0))
    U_dt = expm(-dt*gamma_imp(T1,T2,offset,0,0))
    input_vec = U_90.dot(Liou_vec.ravel()*r_[1,1,1,offset_w])
    input_vec = matrix_power(U_dt,int(pts_delay)).dot(input_vec) # interpulse delay
    input_vec = U_90.dot(U_90).dot(input_vec) # 180 pulse
    for k,echo_num in xrange(nEchoes):
        for j,t_point in enumerate(t2_axis):
            U = expm(-t_point*gamma_imp(T1,T2,offset,0,0))
            fid['Omega',i]['t2',j] = U.dot(input_vec)[1]-1j*U.dot(input_vec)[2]
with figlist_var() as fl:
    fl.next('With inhomogenenous B0')
    fid.sum('Omega')
    fl.plot(fid.real)
    fl.plot(fid.imag)


# In[223]:


#time_len = 1000
#dt = 1.5e-3

T1 = 0.8
T2 = 0.3

delay_time = 0.15
pts_delay = delay_time/dt

acq_time = 2*delay_time
pts_acq = acq_time/dt
t2_axis = r_[0:pts_acq]*dt

nEchoes = 16


# In[241]:


tau = 0.15
tau_pts = tau/dt

acq_time = 2*tau - 2*p90
acq_pts = acq_time/dt
t2_axis = r_[0:acq_pts]*dt

nEchoes = 12
full_t2 = r_[0:acq_pts*nEchoes]*dt


# In[242]:


fid = ndshape([nEchoes,len(offset_axis),len(t2_axis)],['nEchoes','Omega','t2']).alloc()
fid.setaxis('t2',t2_axis)
fid.setaxis('Omega',offset)
fid.setaxis('nEchoes',r_[0:nEchoes])
            
for i,offset_pt in enumerate(offset_axis):
    offset = offset_pt*2*pi
    offset_w = (1./(sigma*sqrt(2*pi)))*exp(-0.5*((offset_pt-mu)/sigma)**2)
    U_90 = expm(-p90*gamma_imp(T1,T2,offset,omega1,0.0))
    U_dt = expm(-dt*gamma_imp(T1,T2,offset,0,0))
    input_vec = U_90.dot(Liou_vec.ravel()*r_[1,1,1,offset_w])
    input_vec = matrix_power(U_dt,int(tau_pts)).dot(input_vec) # interpulse delay
    for k in xrange(nEchoes):
        if k == 0:
            input_vec = U_90.dot(U_90).dot(input_vec) # 180 pulse
            last_rho = input_vec.copy()
        else:
            last_rho = U_90.dot(U_90).dot(last_rho)
        for j,t_point in enumerate(t2_axis):
            fid['nEchoes',k]['Omega',i]['t2',j] = (r_[1,-1j]*last_rho[r_[1,2]]).sum()
            last_rho = U_dt.dot(last_rho)


# In[243]:


fid.sum('Omega')
full_t2 = r_[0:len(t2_axis)*nEchoes]*dt
fid.setaxis('t2',t2_axis)
fid.smoosh(['nEchoes','t2'],'t2')
fid.setaxis('t2',full_t2)


# In[244]:


with figlist_var() as fl:
    fl.next('cpmg')
    fl.plot(fid.real)
    fl.plot(fid.imag)

