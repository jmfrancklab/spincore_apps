from pyspecdata import *
fl = figlist_var()
for date,id_string,PW in [
        ('190116','MWE_1','0.87'), # 10 transients, theta = 0.87 us, d1 = 100 us
        ('190116','MWE_2','0.87'), # 100 transients, theta = 0.87 us, d1 = 100 us
        ('190116','MWE_3','10.44'), # 10 transients, theta = 10.44 us, d1 = 100 us
        ('190116','MWE_4','10.44'), # 100 transients, theta = 10.44 us, d1 = 100 us
        ('190116','MWE_5','2.61'), # 10 transients, theta = 2.61 us, d1 = 100 us
        ('190116','MWE_5_1','2.61'), # 10 transients, theta = 2.61 us, d1 = 500 us
        ('190116','MWE_6','2.61'), # 100 transients, theta = 2.61 us, d1 = 500 us
        ]:
    SW_kHz = 20.0
    nPoints = 64
    filename = date+'_'+id_string+'.h5'
    id_string = id_string.replace('MWE_','Example ') # for plotting purposes
    nodename = 'transients'
    s = nddata_hdf5(filename+'/'+nodename,
            directory = getDATADIR(
                exp_type = 'test_equip'))
    s.set_units('t','s')
    trans_no = len(s.getaxis('trans_no'))
    s.setaxis('trans_no',r_[1:trans_no+1])
    fl.next('Raw data: %s, Pulse Width = %s $\mu$s'%(id_string,PW))
    fl.image(s)
fl.show();quit()
