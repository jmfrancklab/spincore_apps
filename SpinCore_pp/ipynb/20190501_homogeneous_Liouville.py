
# coding: utf-8

# In[ ]:


from pyspecdata import *
from scipy.linalg import expm


# In[ ]:


Iz = 0.5*array([[1,0],[0,-1]],dtype=complex128)
Ix = 0.5*array([[0,1],[1,0]],dtype=complex128)
Iy = 0.5*array([[0,-1j],[1j,0]],dtype=complex128)
E = array([[1,0],[0,1]],dtype=complex128)


# In[ ]:


# E, X, Y, Z, this time based off of Cavanagh (p264, [5.63])
# specifically an x-pulse
def pulse(th):
    matrix_rep = array( [ [1,0,0,0]
                        , [0,cos(th),0,-sin(th)]
                        , [0,0,1,0]
                        , [0,sin(th),0,cos(th)]], dtype=complex128 )
    return matrix_rep


# In[ ]:


def gamma(T1,T2):
    return array([ [0,0,0,0]
                  ,[0,1./T2,0,0]
                  ,[0,0,1./T2,0]
                  ,[-1./T1,0,0,1./T1]
                 ], dtype=complex128)


# In[ ]:


Liou_vec = array([[1],[0],[0],[1]],dtype=complex128)


# In[ ]:


T1_grid = logspace(-3,0,30)
T2_grid = linspace(1e-3,2,30)
results = ndshape([len(T1_grid),len(T2_grid)],['T1','T2']).alloc()
results.setaxis('T1',log10(T1_grid))
results.setaxis('T2',T2_grid)
delay = 10e-3
n_sat = 20
counter = 0
P = pulse(pi/2)
for i,T1 in enumerate(T1_grid):
    for j,T2 in enumerate(T2_grid):
        R = expm(-delay*gamma(T1,T2))
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


# In[ ]:


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

