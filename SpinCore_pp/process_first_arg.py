def process_args(firstarg,
        secondarg = None,
        effective_gamma = 0.0042490577 # MHz/G
        ):
    """process an argument, which can be either a field or a frequency (depending on which is easier
    
    Parameters
    ==========
    firstarg: str repr of a float
        *Either* a field in G or a frequency in *MHz* --> note that these will
        be very different types of numbers (thousands vs. tens respectively),
        so the program can use that to determine. 
    effective_gamma: float
        The effective gamma in MHz/G
    secondarg: str repr of a float
        The second argument from the command line -- this can be used to override the effective_gamma (given here as MHz/T).
        (In the future, we could also use this to allow automatic calculation of NMR from ESR frequency and ppt value.)
    """
    firstarg = float(firstarg)
    if firstarg > 2500: # assume it's a field
        if secondarg is not None:
            effective_gamma = float(secondarg)
            assert effective_gamma > 41 and effective_gamma < 43, "second argument should be effective gamma in MHz/T"
            effective_gamma = effective_gamma/1e4
        field = firstarg
        assert field > 2500 and field < 4000, "first argument should be a field (G) or a frequency (MHz) value!!!"
        carrier_frequency = field*effective_gamma
        print("Using a field of %f and an effective gamma of %g to predict a frequency of %f MHz"%(field,effective_gamma,carrier_frequency))
    elif firstarg > 12 and firstarg < 20:
        carrier_frequency = firstarg
        print("You manually specified a frequency of %f MHz.  The first time you run NMR, you can set your field to %f G"%(carrier_frequency,carrier_frequency/effective_gamma))
    else:
        raise ValueError("not sure what to make of the first argument "+str(firstarg))
    return carrier_frequency

