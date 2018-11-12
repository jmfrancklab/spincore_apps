from pyspecdata import *
fl = figlist_var()
for date,id_string in [
        #('181109','SE_2'), # SW = 10 kHz
        #('181109','test_2') # SW = 10 kHz
        #('181109','test_3'), # SW = 1 kHz
        #('181109','SE_3') # SW = 1 kHz
        #('181109','SE_4'), # SW = 200 kHz
        #('181109','test_4') # SW = 200 kHz
        #('181109','SE_5') # SW = 200 kHz
        #('181110','SE_1'), # SW = 200 kHz
        #('181110','noise_1'), # SW = 200 kHz
        #('181110','noise_2'), # SW = 200 kHz
        #('181110','noise_3'), # SW = 200 kHz
        #('181110','noise_4'), # SW = 200 kHz
        #('181110','noise_5'), # SW = 200 kHz
        #('181110','SE_1'), # SW = 200 kHz
        #('181110','SE_2'), # SW = 200 kHz
        #('181110','SE_3'), # SW = 200 kHz
        #('181110','SE_4'), # SW = 200 kHz
        ('181110','SE_5'), # SW = 200 kHz
        ('181110','SE_6'), # SW = 200 kHz
        ('181110','SE_7'), # SW = 200 kHz
        ('181110','SE_8'), # SW = 200 kHz
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
    #fl.next('SpinCore Spin Echo, %d scan(s)'%nScans)
    #fl.plot(s.real,alpha=0.4,c='r',label='real')
    #fl.plot(s.imag,alpha=0.4,c='blue',label='imag')
    #fl.next('SpinCore Spin Echo, %d scan(s) (zoom)'%nScans)
    #fl.plot(s.real['t':(0,7e-3)],alpha=0.4,c='r',label='real')
    #fl.plot(s.imag['t':(0,7e-3)],alpha=0.4,c='blue',label='imag')
    #axvline(4.9,c='k',linestyle=':')
    fl.next('SpinCore Spin Echoes, 20 scans')
    fl.plot(s['t':(0,40e-3)],alpha=0.4,label='%s'%label)
    #s.ft('t',shift=True)
    #fl.next('capture, f')
    #fl.plot(s,alpha=0.4,label='%s'%label)
fl.show()
