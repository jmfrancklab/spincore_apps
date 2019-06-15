from pyspecdata import *
fl = figlist_var()
date = '190614'
for id_string in [
        ('calibrate_clock_1'),
        ]:
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(exp_type = 'test_equip' ))
    s.rename('t','t2').set_units('t2','s')
    clock_correction = 0
    clock_correction = -0.399405/9.969
    #clock_correction = 1.78/0.99
    fl.next('image raw')
    fl.image(s)
    s *= exp(-1j*s.fromaxis('vd')*clock_correction)
    acq_time = s.getaxis('t2')[-1]
    manual_taxis_zero = acq_time*1e-3/2.0
    s.setaxis('t2',lambda x: x-manual_taxis_zero)
    fl.next('image corrected')
    fl.image(s)
    fl.next('phase error vs vd')
    fl.plot(s.sum('t2').angle, 'o')
    fl.next('phase error, unwrapped vs vd')
    s = s['vd',1:]/s['vd',:-1]
    s = s.angle.name('signal phase').set_units('rad')
    s.data = s.data.cumsum()
    fl.plot(s,'o')
    print (s.data[-1]-s.data[-2])/(s.getaxis('vd')[-1]-s.getaxis('vd')[-2])
fl.show()
