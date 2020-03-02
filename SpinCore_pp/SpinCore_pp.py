# This file was automatically generated by SWIG (http://www.swig.org).
# Version 3.0.12
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.

from sys import version_info as _swig_python_version_info
if _swig_python_version_info >= (2, 7, 0):
    def swig_import_helper():
        import importlib
        pkg = __name__.rpartition('.')[0]
        mname = '.'.join((pkg, '_SpinCore_pp')).lstrip('.')
        try:
            return importlib.import_module(mname)
        except ImportError:
            return importlib.import_module('_SpinCore_pp')
    _SpinCore_pp = swig_import_helper()
    del swig_import_helper
elif _swig_python_version_info >= (2, 6, 0):
    def swig_import_helper():
        from os.path import dirname
        import imp
        fp = None
        try:
            fp, pathname, description = imp.find_module('_SpinCore_pp', [dirname(__file__)])
        except ImportError:
            import _SpinCore_pp
            return _SpinCore_pp
        try:
            _mod = imp.load_module('_SpinCore_pp', fp, pathname, description)
        finally:
            if fp is not None:
                fp.close()
        return _mod
    _SpinCore_pp = swig_import_helper()
    del swig_import_helper
else:
    import _SpinCore_pp
del _swig_python_version_info

try:
    _swig_property = property
except NameError:
    pass  # Python < 2.2 doesn't have 'property'.

try:
    import builtins as __builtin__
except ImportError:
    import __builtin__

def _swig_setattr_nondynamic(self, class_type, name, value, static=1):
    if (name == "thisown"):
        return self.this.own(value)
    if (name == "this"):
        if type(value).__name__ == 'SwigPyObject':
            self.__dict__[name] = value
            return
    method = class_type.__swig_setmethods__.get(name, None)
    if method:
        return method(self, value)
    if (not static):
        if _newclass:
            object.__setattr__(self, name, value)
        else:
            self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)


def _swig_setattr(self, class_type, name, value):
    return _swig_setattr_nondynamic(self, class_type, name, value, 0)


def _swig_getattr(self, class_type, name):
    if (name == "thisown"):
        return self.this.own()
    method = class_type.__swig_getmethods__.get(name, None)
    if method:
        return method(self)
    raise AttributeError("'%s' object has no attribute '%s'" % (class_type.__name__, name))


def _swig_repr(self):
    try:
        strthis = "proxy of " + self.this.__repr__()
    except __builtin__.Exception:
        strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)

try:
    _object = object
    _newclass = 1
except __builtin__.Exception:
    class _object:
        pass
    _newclass = 0


def get_time():
    return _SpinCore_pp.get_time()
get_time = _SpinCore_pp.get_time

def pause():
    return _SpinCore_pp.pause()
pause = _SpinCore_pp.pause

def configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints):
    return _SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
configureTX = _SpinCore_pp.configureTX

def configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps):
    return _SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps)
configureRX = _SpinCore_pp.configureRX

def init_ppg():
    return _SpinCore_pp.init_ppg()
init_ppg = _SpinCore_pp.init_ppg

def stop_ppg():
    return _SpinCore_pp.stop_ppg()
stop_ppg = _SpinCore_pp.stop_ppg

def ppg_element(str_label, firstarg, secondarg=0):
    return _SpinCore_pp.ppg_element(str_label, firstarg, secondarg)
ppg_element = _SpinCore_pp.ppg_element

marker_names = {}
from numpy import *
def apply_cycles(ppg_in,list_of_cycles_found):
#{{{ documentation for apply cycles
    """Recursively apply the phase cycles indicated by elements with tuple form
    ``('pulse',length,cyclename,cycle)``
    where ``cyclename`` is a string and ``cycle`` is a numpy array.

    Assume a list like 0, 90, 180, 270 has been loaded into the phase registers.

    All pulses with the same ``cyclename`` are cycled together.

    Though it's not a useful pulse sequence, this should demonstrate the functionality:

    >>> ppg_list = [('pulse',10,'ph1',r_[0,1,2,3]),
    >>>             ('delay',20),
    >>>             ('pulse',10,'ph1',r_[0,1]),
    >>>             ('delay',10),
    >>>             ('pulse',10,'ph2',r_[0,2]),
    >>>             ('acq',0.5e6)]

    Returns
    -------
    ppg_out: list of tuples
        New pulse program with the phase cycle applied.
    list_of_cycles_found: list of tuples
        List of cycles found that could be used to reshape the data.
        The list is given outside in, so that it's in the right order.
    """
#}}}
    pulse_cycles = []
    found_cycle = False
    for cycled_idx, ppg_element in enumerate(ppg_in):
        if (len(ppg_element)>3) and (ppg_element[0] == 'pulse' or ppg_element[0] == 'pulse_TTL') and (type(ppg_element[2]) is str):
            cycle_name = ppg_element[2]
            found_cycle = True
            break
    if found_cycle:
        print("found phase cycle named",cycle_name)
        all_cycles = [ppg_element[3] for ppg_element in ppg_in if (((ppg_element[0] == 'pulse' or ppg_element[0] == 'pulse_TTL') and ppg_element[2] == cycle_name) if len(ppg_element)>3 else False )]
        maxlen = max(map(len,all_cycles))
        list_of_cycles_found = [(cycle_name,maxlen)] + list(list_of_cycles_found)
        print("LIST OF CYCLES FOUND NOW")
        ppg_out = []
        for j in range(maxlen):
            for k,ppg_elem in enumerate(ppg_in):
                if len(ppg_elem) > 3 and ppg_elem[2] == cycle_name:
                    elem_copy = list(ppg_elem)
                    spec_len = len(elem_copy[3])
                    c_idx = j % spec_len
                    ppg_out.append(tuple(elem_copy[:2]+[elem_copy[3][c_idx].item()]))
                else:
                    ppg_out.append(ppg_elem)
        del ppg_in
        print("***")
        print("AFTER CYCLING:\n",'\n'.join(map(str,ppg_out)))
        return apply_cycles(ppg_out,list_of_cycles_found)
    else:
        print("***")
        print("FOUND NO CYCLING ELEMENTS")
        return ppg_in,list_of_cycles_found
def load(args):
    ppg_list = []
    for a_tuple in args:
        if a_tuple[0] == 'marker':
            a_tuple = list(a_tuple)
            marker_idx = len(marker_names)
            marker_names[a_tuple[1]] = marker_idx 
            a_tuple[1] = marker_idx
            a_tuple = tuple(a_tuple)
        elif a_tuple[0] == 'jumpto':
            a_tuple = list(a_tuple)
            marker_idx = marker_names[a_tuple[1]]
            a_tuple[1] = marker_idx
            a_tuple = tuple(a_tuple)
        ppg_list.append(a_tuple)
    ppg_list,list_of_cycles_found = apply_cycles(ppg_list,[])
    for a_tuple in ppg_list:
        ppg_element(*a_tuple)


def runBoard():
    return _SpinCore_pp.runBoard()
runBoard = _SpinCore_pp.runBoard

def getData(output_array, nPoints, nEchoes, nPhaseSteps, output_name):
    return _SpinCore_pp.getData(output_array, nPoints, nEchoes, nPhaseSteps, output_name)
getData = _SpinCore_pp.getData

def stopBoard():
    return _SpinCore_pp.stopBoard()
stopBoard = _SpinCore_pp.stopBoard

def tune(carrier_freq):
    return _SpinCore_pp.tune(carrier_freq)
tune = _SpinCore_pp.tune
# This file is compatible with both classic and new-style classes.


