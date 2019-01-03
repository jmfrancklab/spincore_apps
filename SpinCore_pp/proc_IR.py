from pyspecdata import *
from scipy.optimize import minimize
fl = figlist_var()
date = '190102'
id_string = 'IR_ph2'
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
s.setaxis('t2',None)
s.chunk('t2',['ph2','ph1','t2'],[4,2,-1])
s.setaxis('t2',t2_axis[nPoints])
s.setaxis('ph1',r_[0,2])
s.setaxis('ph2',r_[0,1,2,3])
print ndshape(s)
fl.next('image')
fl.image(s)
s.ft(['ph2','ph1'])
fl.next('image coherence')
fl.image(s)
data = s['ph2',1]['ph1',0].C
fl.next('plot data')
fl.image(abs(data))
min_index = abs(data).run(sum,'t2').argmin('vd',raw_index=True).data
min_vd = data.getaxis('vd')[min_index]
est_T1 = min_vd/log(2)
print "Estimated T1 is:",est_T1,"s"
fl.show();quit()
