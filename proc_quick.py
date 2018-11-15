from pyspecdata import *
fl = figlist_var()
for date,id_string in [
        ('181114','nutation_1'),
        ]:
    filename = date+'_'+id_string+'.h5'
    nodename = 'signal'
    with open(getDATADIR(exp_type='test_equip')+date+'_'+id_string+'_params.txt', "r") as F:
        for line in F:
            if 'tauDelay_us=' in line:
                temp = line.strip().split()
                temp = temp[1].split('=')
                tauDelay_us = float(temp[1])
            if 'nScans=' in line:
                temp = line.strip().split()
                temp = temp[1].split('=')
                nScans = int(temp[1])
    label=r'$\tau$=%0.1f ms'%(tauDelay_us/1e3)
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    s.set_units('t','s')
    fl.next('Plotting nutation')
    fl.plot(abs(s))
    s.ft('t',shift=True)
    fl.next('F plot')
    fl.plot(s)
    s = s['t':(-10e3,10e3)]
    s.ift('t')
    fl.next('Filtered')
    fl.plot(abs(s))
    fl.show();quit()
    #fl.next('SpinCore Spin Echo, %d scan(s)'%nScans)
    #fl.plot(s.real,alpha=0.4,c='r',label='real')
    #fl.plot(s.imag,alpha=0.4,c='blue',label='imag')
    #fl.next('SpinCore Spin Echo, %d scan(s) (zoom)'%nScans)
    #fl.plot(s.real['t':(0,7e-3)],alpha=0.4,c='r',label='real')
    #fl.plot(s.imag['t':(0,7e-3)],alpha=0.4,c='blue',label='imag')
    #axvline(4.9,c='k',linestyle=':')
    fl.next('SpinCore CPMG, 16 echoes')
    fl.plot(s['t':(0,40e-3)],alpha=0.4,label='%s'%label)
    #s.ft('t',shift=True)
    #fl.next('capture, f')
    #fl.plot(s,alpha=0.4,label='%s'%label)
fl.show()
