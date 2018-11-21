from pyspecdata import *
fl = figlist_var()
for date,id_string in [
        ('181121','nutation_2'),
        #('181120','nutation_2'),
        #('181120','nutation90_1'),
        #('181114','nutation_5'),
        #('181113','CPMG_8'),
        ]:
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    with open(getDATADIR(exp_type='test_equip')+date+'_'+id_string+'_params.txt', "r") as F:
        for line in F:
            if 'nPoints=' in line:
                temp = line.strip().split()
                temp = temp[1].split('=')
                nPoints = float(temp[1])
            if 'nPoints_Nutation=' in line:
                temp = line.strip().split()
                temp = temp[1].split('=')
                nPoints_Nutation = int(temp[1])
            if 'tauDelay_us=' in line:
                temp = line.strip().split()
                temp = temp[1].split('=')
                tauDelay_us = float(temp[1])
            if 'nScans=' in line:
                temp = line.strip().split()
                temp = temp[1].split('=')
                nScans = int(temp[1])
            if 'nutation_step=' in line:
                temp = line.strip().split()
                temp = temp[1].split('=')
                nutation_step = float(temp[1])
            if 'p90Time_us=' in line:
                temp = line.strip().split()
                temp = temp[1].split('=')
                p90Time_us = float(temp[1])
    label=r'$\tau$=%0.1f ms'%(tauDelay_us/1e3)
    is_Nutation = False
    if 'nutation' in id_string:
        is_Nutation = True
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    s.set_units('t','s')
    #{{{ for nutation data
    if is_Nutation:
        fl.next('raw data pull')
        fl.plot(s.real,alpha=0.5,label='real')
        fl.plot(s.imag,alpha=0.5,label='imag')
        fl.next('raw data, abs')
        fl.plot(abs(s))
        t_axis = s.getaxis('t')
        s.setaxis('t',None)
        s.chunk('t',['PW','t2'],[nPoints_Nutation,nPoints])
        t2_axis = t_axis[0:int(nPoints)]
        PW_axis = []
        for x in xrange(nPoints_Nutation):
            temp = p90Time_us*(x+1)*nutation_step*1e-6
            PW_axis.append(temp)
        s.setaxis('t2',t2_axis).set_units('t2','s')
        s.setaxis('PW',PW_axis)
        s.reorder('t2',first=False)
        #{{{ Try to phase
        s_ph = s['PW',2].C
        fl.next('single')
        s_ph.ft('t2',shift=True)
        ph_corr = exp(1j*2*pi*0.3)
        s_ph *= ph_corr
        s_ph.ift('t2')
        fl.plot(s_ph, alpha=0.5)
        fl.plot(s_ph.imag, alpha=0.5)
        #}}}
        s.ft('t2',shift=True)
        s *= ph_corr
        #s = s['t2':(-5e3,5e3)]
        s.ift('t2')
        fl.next('image nutation, abs')
        fl.image(abs(s))
        fl.next('image nutation')
        fl.image(s)
        fl.show();quit()
        fl.next('Plotting nutation')
        fl.plot(abs(s))
        s.ft('t',shift=True)
        fl.next('F plot')
        fl.plot(s)
        s *= exp(1j*2*pi*pi*1.01)
        s = s['t':(-5e3,5e3)]
        s.ift('t')
        fl.next('Filtered')
        fl.plot(s.real)
        fl.plot(s.imag)
        fl.show();quit()
        #}}}
    #fl.next('SpinCore Spin Echo, %d scan(s)'%nScans)
    fl.next('CPMG')
    fl.plot(s.real,alpha=0.4,c='r',label='real')
    fl.plot(s.imag,alpha=0.4,c='blue',label='imag')
    fl.next('SpinCore Spin Echo, %d scan(s) (zoom)'%nScans)
    fl.plot(s.real['t':(0,7e-3)],alpha=0.4,c='r',label='real')
    fl.plot(s.imag['t':(0,7e-3)],alpha=0.4,c='blue',label='imag')
    axvline(4.9,c='k',linestyle=':')
    fl.next('CPMG, 16 echoes')
    fl.plot(s['t':(0,40e-3)],alpha=0.4,label='%s'%label)
    #s.ft('t',shift=True)
    #fl.next('capture, f')
    #fl.plot(s,alpha=0.4,label='%s'%label)
fl.show()
