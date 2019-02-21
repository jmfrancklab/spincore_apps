from pyspecdata import *
fl = figlist_var()
for date,id_string in [
        #('190220','FS_6_on'),
        #('190220','FS_6_off'),
        #('190220','FS_6_on_2'),
        #('190220','FS_6_on_3'),
        #('190220','FS_6_on_4'),
        #('190220','FS_8'),
        #('190220','FS_9'),
        #('190220','FS_10'),
        ('190220','FS_11'),
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
    fl.next('raw ft ph, chunk'+id_string)
    fl.image(s)
    s.ft('t2',shift=True)
    fl.next('raw ft ph, chunk freq'+id_string)
    fl.image(s['t2':(-20e3,20e3)])
    s = s['ph2',0]['ph1',1].C
    fl.next('coherence')
    fl.image(s['t2':(-20e3,20e3)])
    fl.show();quit()
    #s.ift('t2')
    #fl.show();quit()
    #s = s['ph2',0]['ph1',1].C
    #fl.next('coh ch, time'+id_string)
    #fl.image(abs(s['t2':(1.8e-3,2.2e-3)]))
    #s.ft('t2')
    #fl.next('coh ch, freq'+id_string)
    #fl.image(abs(s))
    #s.ift('t2')
    #fl.next('data'+id_string)
    #fl.plot(s.real['field',-3],alpha=0.5)
    #fl.plot(s.imag['field',-3],alpha=0.5)
fl.show();quit()
    ###s.ft('t',shift=True)
    ###time_shift = False
    ###if time_shift:
    ###offset_plot_shift = s.C
    ###offset_plot_shift *= exp(1j*2*pi*s.fromaxis('t')*2e-3)
    ###offset_plot_shift.setaxis('t', lambda x: x/(gammabar_H)*1e4).set_units('t','G')
    ###offset_plot_shift.rename('t',r'$\frac{\Omega}{\gamma_{H}}$')
    ###offset_plot = s.C
    #### gammabar_H is in units of Hz/T
    ###offset_plot.setaxis('t', lambda x: x/(gammabar_H)*1e4).set_units('t','G')
    ###offset_plot.rename('t',r'$\frac{\Omega}{\gamma_{H}}$')
    ###fl.next('offset')
    ###fl.plot(offset_plot['field',2],alpha=0.35,label=r'$B_{0} = %0.1f G$ (raw)'%offset_plot.getaxis('field')[2])
    ###if time_shift:
    ###fl.plot(offset_plot_shift['field',2],alpha=0.35,label=r'$B_{0} = %0.1f G$ (time shift)'%offset_plot.getaxis('field')[2])
    ###print ndshape(offset_plot)
    ###offset_plot.reorder('field', first=True)
    ###fl.next('sweep, image plot abs (offset)')
    ###fl.image(abs(offset_plot))
    ###fl.next('sweep, image plot (offset)')
    ###fl.image(offset_plot)
    ###if time_shift:
    ###offset_plot_shift.reorder('field', first=True)
    ###fl.next('sweep, image plot abs (offset, time shift)')
    ###fl.image(abs(offset_plot_shift))
    ###fl.next('sweep, image plot (offset, time shift)')
    ###fl.image(offset_plot_shift)
    ###s.ift('t')
    ###s.reorder('t', first=False)
    ###fl.next('sweep, image plot abs (time)')
    ####fl.image(abs(s['t':(0,4e-3)]))
    ###fl.image(abs(s))
    ###fl.next('sweep, image plot (time)')
    ####fl.image(s['t':(0,4e-3)])
    ###fl.image(s)
    ###fl.next('data')
    ###fl.plot(s.real['field',-3])
    ###fl.plot(s.imag['field',-3])
    ###fl.show();quit()
    ###s.ft('t')
    ###print ndshape(s)
    ###s.reorder('t',first=True)
    ###print ndshape(s)
    ####fl.plot(abs(s)['field':3418.0])
    ###fl.show()
