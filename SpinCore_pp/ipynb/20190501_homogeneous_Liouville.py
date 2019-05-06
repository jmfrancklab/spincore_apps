
# coding: utf-8

# In[ ]:


from pyspecdata import *
from scipy.linalg import expm


# In[ ]:


# Operators

Iz = 0.5*array([[1,0],[0,-1]],dtype=complex128)
Ix = 0.5*array([[0,1],[1,0]],dtype=complex128)
Iy = 0.5*array([[0,-1j],[1j,0]],dtype=complex128)
E = array([[1,0],[0,1]],dtype=complex128)


# In[ ]:


# RF pulse matrix in rotating frame
#E, X, Y, Z, this time based off of Cavanagh (p264, [5.63])
#specifically an x-pulse
def pulse(th):
    matrix_rep = array( [ [1,0,0,0]
                        , [0,cos(th),0,-sin(th)]
                        , [0,0,1,0]
                        , [0,sin(th),0,cos(th)]], dtype=complex128 )
    return matrix_rep


# In[ ]:


# RF pulse matrix in rotating frame, for 4-step phase cycle
def pulse(phase,theta):
    if 'x' in phase:
        matrix_rep = array([ [1,0,0,0]
                           , [0,cos(theta),0,-sin(theta)]
                           , [0,0,1,0]
                           , [0,sin(theta),0,cos(theta)]], dtype=complex128)

        if phase == '-x':
            matrix_rep[1,-1] = matrix_rep[1,-1]*-1
            matrix_rep[-1,1] = matrix_rep[1,-1]*-1
            return matrix_rep
        else:
            return matrix_rep
    elif 'y' in phase:
        matrix_rep = array( [ [1,0,0,0]
            , [0,1,0,0]
            , [0,0,cos(theta),-sin(theta)]
            , [0,0,sin(theta),cos(theta)]], dtype=complex128 )
        if phase == '-y':
            matrix_rep[2,-1] = matrix_rep[2,-1]*-1
            matrix_rep[-1,2] = matrix_rep[2,-1]*-1
            return matrix_rep
        else:
            return matrix_rep
    else:
        print "Cannot understand specified phase of rf pulse"


# In[ ]:


# RF pulse matrix with relaxation, in rotating frame
#including relaxation
def pulse_imp(th,T1,T2):
    matrix_rep = array( [ [1,0,0,0]
                        , [0,cos(th)+(1./T2),0,-sin(th)]
                        , [0,0,1+(1./T2),0]
                        , [-1./T1,sin(th),0,cos(th)+(1./T1)]], dtype=complex128 )
    return matrix_rep


# In[ ]:


# Relaxation matrix
#standard relaxation superoperator
def gamma(T1,T2):
    return array([ [0,0,0,0]
                  ,[0,1./T2,0,0]
                  ,[0,0,1./T2,0]
                  ,[-1./T1,0,0,1./T1]
                 ], dtype=complex128)


# In[ ]:


# Improved relaxation matrix
#Improved relaxation superoperator
#Note, can either re-arrange the upper 4x4 in [30] of Allard and Hard 2001
#or can rearrange the general form provided on p13 in Cavanagh,
#either way, working in the rotating frame
#offset refers to amount off resonance (function of B0)
#freq is a function of B1

def gamma_imp(T1,T2,offset,omega1):
    return array([ [0,0,0,0]
                  ,[0,1./T2,-offset,-omega1]
                  ,[0,offset,1./T2,omega1]
                  ,[-1./T1+omega1,-omega1,0,1./T1]
                 ], dtype=complex128)


# In[ ]:


Liou_vec = array([[1],[0],[0],[1]],dtype=complex128)


# In[ ]:


# just relaxation
T1_grid = logspace(-3,0,30)
T2_grid = linspace(1e-3,2,30)
results = ndshape([len(T1_grid),len(T2_grid),4],['T1','T2','ph']).alloc()
results.setaxis('T1',log10(T1_grid))
results.setaxis('T2',T2_grid)
results.setaxis('ph',r_[0:4])
delay = 10e-3
n_sat = 20
offset = 0
freq = 0
#P = pulse_imp(pi/2,T1,T2)
for h,rf_phase in enumerate(['x','y','-x','-y']):
    for i,T1 in enumerate(T1_grid):
        for j,T2 in enumerate(T2_grid):
            P = pulse(rf_phase,pi/2)
            R = expm(-delay*gamma(T1,T2))
            R = complex128(R)
            equil_vec = array([[1],[0],[0],[1]],dtype=complex128)
            result = equil_vec
            for k in xrange(n_sat-1):
                result = P.dot(result)
                result = R.dot(result)
            results['T1',i]['T2',j]['ph',h] = P.dot(result)[1]-1j*P.dot(result)[2]
    #results.rename('T1','$log_{10}(T_1)$')
    with figlist_var() as fl:
        fl.next('results'+rf_phase)
        fl.image((results['ph',h]))


# In[ ]:


# still just relaxation, using improved relaxation superoperator
T1_grid = logspace(-3,0,30)
T2_grid = linspace(1e-3,2,30)
results = ndshape([len(T1_grid),len(T2_grid)],['T1','T2']).alloc()
results.setaxis('T1',log10(T1_grid))
results.setaxis('T2',T2_grid)
delay = 10e-3
n_sat = 20
offset = 0
freq = 0
#P = pulse_imp(pi/2,T1,T2)
for i,T1 in enumerate(T1_grid):
    for j,T2 in enumerate(T2_grid):
        P = pulse('x',pi/2)
        R = expm(-delay*gamma_imp(T1,T2,offset,freq))
        R = complex128(R)
        equil_vec = array([[1],[0],[0],[1]],dtype=complex128)
        result = equil_vec
        for k in xrange(n_sat-1):
            result = P.dot(result)
            result = R.dot(result)
        results['T1',i]['T2',j] = P.dot(result)[1]-1j*P.dot(result)[2]

results.rename('T1','$log_{10}(T_1)$')
with figlist_var() as fl:
    fl.next('results')
    fl.image(abs(results))


# Got expected result using Cavanagh rotation matrix

# In[ ]:


Liou_vec = array([[1],[0],[0],[1]],dtype=complex128)


# In[ ]:


interpulse = 1
T1_log = linspace(-3,10,100) # units of intp_delay
T2_log = linspace(-3,8,100) # units of intp_delay

results = ndshape([len(T1_log),len(T2_log)],['T1','T2']).alloc()
results.rename('T1',r'$log_{10}(\frac{T_{1}}{interpulse})$')
results.rename('T2',r'$log_{10}(\frac{T_{2}}{interpulse})$')
results.setaxis(r'$log_{10}(\frac{T_{1}}{interpulse})$',T1_log)
results.setaxis(r'$log_{10}(\frac{T_{2}}{interpulse})$',T2_log)

T1_grid = 10**(T1_log)
T2_grid = 10**(T2_log)

P = pulse(pi/2)

for n_sat in xrange(0,50,2):
    for i,T1 in enumerate(T1_grid):
        for j,T2 in enumerate(T2_grid):
            R = expm(-interpulse*gamma(T1,T2))
            eq_vec = Liou_vec
            result = eq_vec
            for k in xrange(n_sat-1):
                result = P.dot(result)
                result = R.dot(result)
            results[r'$log_{10}(\frac{T_{1}}{interpulse})$',i][r'$log_{10}(\frac{T_{2}}{interpulse})$',j] = P.dot(result)[-1]
    with figlist_var() as fl:
        figure()
        fl.next('results n_sat=%d'%(n_sat),figsize=(14,8))
        fl.image(results.real, vmin=-1, vmax=1)

