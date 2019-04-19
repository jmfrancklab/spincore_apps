from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping
fl = figlist_var()
for date,id_string in [
        ('190418','echo_9_1'),
        ]:
    nPoints = 256
    nEchoes = 1
    nPhaseSteps = 8
    SW_kHz = 15.0
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    print ndshape(s)
    s.set_units('t','s')
    orig_t = s.getaxis('t')
    acq_time_s = orig_t[nPoints]
    t2_axis = linspace(0,acq_time_s,nPoints)
    s.setaxis('t',None)
    s.reorder('t',first=True)
    s.chunk('t',['ph2','ph1','t2'],[2,4,-1])
    s.setaxis('ph2',r_[0.,2.]/4)
    s.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    s.setaxis('t2',t2_axis)
    s.reorder('t2',first=False)
    #fl.next('raw data - chunking')
    #fl.image(s)
    s.ft('t2',shift=True)
    s.ft(['ph1','ph2'])
    fl.next(id_string+'raw data - chunking coh')
    fl.image(s)
    s = s['ph1',1]['ph2',0].C
    s.setaxis('t2',s.getaxis('t2'))
    fl.next('freq-signal')
    fl.plot(s.real)
    fl.plot(s.imag)
    s.ift('t2')
    fl.next('time-signal')
    fl.plot(s.real)
    fl.plot(s.imag)
    fl.show();quit()
fl.show()
