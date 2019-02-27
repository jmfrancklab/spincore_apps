from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping
fl = figlist_var()
for date,id_string in [
        ('190226','echo_8'),
        #('190225','echo_3'),
        ]:
    nPoints = 128 
    nEchoes = 1
    nPhaseSteps = 8
    SW_kHz = 80.0
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    print ndshape(s)
    s.set_units('t','s')
    orig_t = s.getaxis('t')
    acq_time_s = orig_t[nPoints]
    fl.next('raw data')
    fl.plot(s.real,alpha=0.4)
    fl.plot(s.imag,alpha=0.4)
    fl.plot(abs(s),':',c='k',alpha=0.4)
    t2_axis = linspace(0,acq_time_s,nPoints)
    s.setaxis('t',None)
    s.reorder('t',first=True)
    s.chunk('t',['ph2','ph1','t2'],[2,4,-1])
    s.setaxis('ph2',r_[0.,2.]/4)
    s.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    s.setaxis('t2',t2_axis)
    s.reorder('t2',first=False)
    fl.next('raw data - chunking')
    fl.image(s)
    s.ft('t2',shift=True)
    s.setaxis('t2',lambda f: f+35e3)
    s.ft(['ph1','ph2'])
    fl.next(id_string+'raw data - chunking coh')
    fl.image(s)
    s *= exp(-1j*2*pi*s.fromaxis('t2')*0.045)
    ph0 = s.real.sum('t2').C
    s /= ph0
    s = s['t2':(-5e3,5e3)].C
    #s.ift('t2')
    fl.next('view')
    fl.plot(s.real['ph2',0]['ph1',1],'.')
    fl.plot(s.imag['ph2',0]['ph1',1],'.')

    fl.show();quit()
    fl.next('time domain data')
    fl.plot(s.real['ph2',0]['ph1',1])
    fl.plot(s.imag['ph2',0]['ph1',1])
    s.ft('t2',shift=True)
    fl.next(id_string+'data - FT')
    fl.image(s)
    s = s['ph2',0]['ph1',1].C
    fl.next(id_string+'data time')
    fl.plot(s.real)
    fl.plot(s.imag)
fl.show()
