from pyspecdata import *
import numpy as np

# {{{ number of steps, etc
FIR = True
ODNP = True 
nT1 = 5
nScans_FIR = 1 # this should generally *not* be the same as the next parameter!
nScans_ODNP = 1
nPhaseSteps = 4
vd_len = 12
power_len = 15
# }}}
# {{{ relaxation parameters that can change from sample to sample
C_SL = 50e-6
krho = 353. # this number for small SL -- check against PNMRS
kHH = 0 # e.g. if we have a protein and we have relaxation due to the protein
C_HH = 0 # concentration of the previous thing -- for a protein, this is the
#          same as C_SL, for a lipid it would be different, for an RM I would
#          just leave this alone and override R1water and R1water_hot
R1water = 1./2.2 
R1water_hot = 1./2.2 # check this number with AB
# }}}
# {{{ not to be adjusted -- here we're calculating the relaxation times based
# on the previous, which is what you should always be doing
R1_cold = kHH*C_HH + krho*C_SL + R1water
R1_hot = kHH*C_HH + krho*C_SL + R1water_hot
ODNP_rd = 5/R1_hot
FIR_rd = 2/R1_hot # recommendation for W in Gupta
# }}}
#{{{ calculate timing for FIR
if FIR:
    # JF -- what does Gupta say about the range that we should be using for τ?
    # Here, I just guess that we want to run from 0 to 2*T1_est, but in Becker
    # et al (1980) on pg 382, their item #4 tells us that they do determine the
    # optimal list of τ for a few different cases, and I'm pretty sure one of
    # them is the linear case
    vd_list = (np.linspace(5e-6,FIR_rd,vd_len))
    print('-'*10+'FIR'+'-'*10)
    print("specify this vdlist:  r_[",', '.join(str(j) for j in list(vd_list*1e6)),"]")
    print("use this rd: ",FIR_rd)
    expt = FIR_rd*nScans_FIR*nPhaseSteps*len(vd_list)+sum(vd_list*nPhaseSteps*nScans_FIR)
    print("Estimated experiment time for 1 FIR:",expt/60.,"min.")
    FIR_expt = expt

