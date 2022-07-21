import sys
from numpy import r_, double, linspace

def return_vdlist(
        T1_min, # Ta in Weiss
        T1_max, # Tb in Weiss
        IR_steps = 8, # not distinguising "IR" vs "FIR" here
        startconstant=0.15, # from Weiss via jf_dnpconf au program,
        stopconstant=2.0, # see below
        ):
    """return a vdlist as recommended by Weiss

    (this is linearly spaced, if you want
    logarithmic, and are not doing a sample
    that has two very different T₁ values, you
    should really question your life choices.)

    Parameters
    ----------

    T1_max:
        The maximum T₁ value that you might
        expect.  For ODNP, this typically means
        the same as hot T₁.
        (In Weiss, you think about having a T₁
        in some possible range of values, and
        figuring out what it actually is.)
    T1_min:
        The minimum T₁ value that you might
        expect.
        For ODNP, this is typically the value
        expected at 17 or 18°C.
    startconstant:
        Fraction of smaller T1 value to start
        vdlist at (0.15 recommended).
    stopconstant:
        Fraction of larger T1 value to stop
        vdlist at.

        Weiss recommends 0.75, which only gives 5% recovery -- we choose 2.0,
        since it gives 73% recovery, and that makes us feel better
    """
    taustart = startconstant*T1_min
    # jf_dnp does this, which is equivalent to following
    # (this is not commented code, it's explanation of the code in terms of the
    # symbols used in Weiss)
    # alpha = T1_max/T1_min
    # taustop = stopconstant*alpha*T1_min
    taustop = stopconstant*T1_max
    # again, jf_dnp does this, equiv to following
    # tau = r_[0:IR_steps]
    # tau = taustart + (taustop-taustart)*tau/(IR_steps-1.0);
    return linspace(taustart,taustop,IR_steps)
def vdlist_from_relaxivities(conc,
        krho_cold=380., # err towards higher, since this goes towards estimating the min T1
        krho_hot=260., # err towards lower, since this goes towards estimating the max T1
        T1water_cold=2.17,
        T1water_hot=2.98):
    T1_min = 1.0/(conc*krho_cold+1.0/T1water_cold)
    T1_max = 1.0/(conc*krho_hot+1.0/T1water_hot)
    print(f"for {conc} M of spin label, I calculate a T1_min={T1_min} and T1_max={T1_max}")
    return return_vdlist(T1_min,T1_max)
def print_tempo_vdlist():
    assert len(sys.argv) == 2
    conc = float(sys.argv[1]) 
    print(vdlist_from_relaxivities(conc))
