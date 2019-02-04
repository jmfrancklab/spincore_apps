from pyspecdata import *
fl = figlist_var()
for date,id_string,PW in [
        ('190131','MWE_B0ON','2.0'), # 100 transients, theta = 10.44 us, d1 = 120 us
        ('190131','MWE_B0OFF','2.0'), # 100 transients, theta = 10.44 us, d1 = 120 us
        ]:
    SW_kHz = 20.0
    nPoints = 64
    filename = date+'_'+id_string+'.h5'
    if 'B0ON' in id_string:
        id_string = 'Field On'
    if 'B0OFF' in id_string:
        id_string = 'Field Off'
    #id_string = id_string.replace('MWE_','Example ') # for plotting purposes
    nodename = 'transients'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    s.set_units('t','s')
    trans_no = len(s.getaxis('trans_no'))
    s.setaxis('trans_no',r_[1:trans_no+1])
    #fl.next('Raw data: %s, Pulse Width = %s $\mu$s'%(id_string,PW))
    fl.next('Raw data: %s, Pulse Width = %s $\mu$s'%(id_string,PW))
    fl.image(s)
    #fl.next('real')
    #s.real.waterfall()
    #fl.next('imag')
    #s.imag.waterfall()
    #fl.next('abs')
    #abs(s).waterfall()
fl.show();quit()
