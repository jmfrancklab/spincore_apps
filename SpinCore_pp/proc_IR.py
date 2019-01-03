from pyspecdata import *
from scipy.optimize import minimize
fl = figlist_var()
date = '190102'
id_string = 'test_IR_2'
filename = date+'_'+id_string+'.h5'
nodename = 'signal'
s = nddata_hdf5(filename+'/'+nodename,
        directory = getDATADIR(exp_type = 'test_equip' ))
s.rename('t','t2').set_units('t2','s')
fl.next('raw data - no clock correction')
fl.image(s)
s.ft('t2',shift=True)
clock_correction = -10.51/6 # radians per second
s *= exp(-1j*s.fromaxis('vd')*clock_correction)
s.ift('t2')
fl.next('raw data - clock correction')
fl.image(s)
nPoints = 128
t2_axis = s.getaxis('t2')
fl.next('plot')
for x in xrange(3):
    fl.plot(abs(s)['vd',x])
fl.show();quit()
s.setaxis('t2',None)
s.chunk('t2',['ph1','t2'],[4,-1])
s.setaxis('t2',t2_axis[nPoints])
s.setaxis('ph1',r_[0,1,2,3])
fl.next('image')
fl.image(s)
s.ft(['ph1'])
fl.next('image coherence')
fl.image(s)
data = s['ph1',-1].C
fl.next('plot data')
fl.plot(abs(data))
data.ft('t2',shift=True)
fl.next('plot data freq')
fl.plot(data)
fl.show();quit()
s.ft('t2',shift=True)
f_axis = s.getaxis('t2')
s.ift('t2')
SWH = diff(r_[f_axis[0],f_axis[-1]])[0]
test_plot = False
