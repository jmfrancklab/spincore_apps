from pyspecdata import *
fl = figlist_var()
for date,id_string in [
        ('190419','FS_2'),
        ]:
    filename = date+'_'+id_string+'.h5'
    nodename = 'field_sweep'
    s = nddata_hdf5(filename+'/'+nodename,
        directory = getDATADIR(exp_type = 'test_equip' ))
    s.set_units('t','s')
    nPoints = 2048 # copy from pp
    orig_t = s.getaxis('t')
    acq_time_s = orig_t[nPoints]
    t2_axis = linspace(0,acq_time_s,nPoints)
    s.setaxis('t',None)
    s.reorder('t',first=True)
    s.chunk('t',['ph2','ph1','t2'],[2,4,-1])
    s.setaxis('ph2',r_[0.,2.]/4)
    s.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    s.setaxis('t2',t2_axis)
    s.set_units('field','G')
    print ndshape(s)
    s.reorder('t2',first=False)
    fl.next('raw, chunk'+id_string)
    fl.image(s)
    s.ft(['ph2','ph1'])
    print ndshape(s)
    fl.next('raw ft ph, chunk'+id_string)
    fl.image(s)
    s.ft('t2',shift=True)
    s_offset = s.C
    s_offset.setaxis('t2', lambda f: f/(gammabar_H)*1e4)
    s_offset.set_units('t2','G')
    s_offset.rename('t2',r'$\frac{\Omega}{\gamma_{H}}$')
    fl.next('image, all coherence channels')
    fl.image(s_offset[r'$\frac{\Omega}{\gamma_{H}}$':(-3,3)])
    fl.next('image, $\Delta c_{1}$ = 1, $\Delta c_{2}$ = 0')
    fl.image(s_offset['ph2',0]['ph1',1])
    fl.next('not offset')
    fl.image(s['ph2',0]['ph1',1])
fl.show();quit()
