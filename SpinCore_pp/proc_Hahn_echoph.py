from pyspecdata import *
from scipy.optimize import leastsq,minimize,basinhopping
fl = figlist_var()
for date,id_string in [
        ('190226','echo_7'),
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
    #fl.next('raw data')
    #fl.plot(s.real,alpha=0.4)
    #fl.plot(s.imag,alpha=0.4)
    #fl.plot(abs(s),':',c='k',alpha=0.4)
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
    s.ft('t2',shift=True,pad=256)
    s.setaxis('t2',lambda f: f+35e3)
    s.ft(['ph1','ph2'])
    #fl.next(id_string+'raw data - chunking coh')
    #fl.image(s)
    s *= exp(-1j*2*pi*s.fromaxis('t2')*0.495)
    s *= exp(-1j*pi)
    #s *= exp(1j*2*pi*s.fromaxis('t2')*0.505)
    #s['t2':(8e3,75e3)] = 0
    #s = s['t2':(None,72e3)].C
    if id_string is 'echo_7':
        id_string = 'unenhanced'
        kwargs = {'c' : 'blue'}
    elif id_string is 'echo_8':
        id_string = 'enhanced'
        kwargs = {'c' : 'red'}
    fl.next('ODNP Enhancement of H$_{2}$O')
    #fl.plot(x.real['ph2',0]['ph1',1],**kwargs)
    s *= -1
    fl.plot(s.real['t2':(-3e3,3e3)]['ph2',0]['ph1',1],**kwargs)
fl.show()
