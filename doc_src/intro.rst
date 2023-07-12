If you're uncertain, start with examples!

.. toctree::

    auto_examples/index

The processing is structured into multiple levels.

Lowest level
============

At the lowest level lives `pySpecData
<http://jmfrancklab.github.io/pyspecdata>`_, which
provides an object-oriented structure (nddata) for
storing all information about code (*e.g.* data, error,
axes, units, and names of dimensions) in a single
"container" (technically called an "object"), as well
as routines ("methods") for manipulating that data
(doing things like Fourier transforming, taking sums,
etc. etc.).
pySpecData provides a fundamentally unique was of
dealing with spectroscopic data in Python
(it enables things like ``d['t2':(0.1,0.5)]`` to slice
out times from 0.1 to 0.5 s, automatic relabeling of
axes during a Fourier transform, and automatic
propagation of error, to name a few).
If there are more efficient ways of dealing with axes,
specifying data slices, dealing with Fourier *vs.*
time-domain data, these are all implemented at the
pySpecData level (which lives in a different repository
than the application scripts here).

First level in this repo
========================

Currently, we have the following modules that provide
functions intended to be reused.  We will refer to
these as "first level" routines:

.. toctree::

    first_level/phasing
    first_level/align


Second level in this repo
=========================

We are currently in the process of identifying the most
up to date code that does each of the following tasks,
and each will be separated into a function inside an
appropriate module, and added to the previous list.
At least parts of this should be relevant to most
data processing tasks involving ODNP or relaxometry.
We will refer to these as "second level"
routines, since they use the "first level" routines:

-  load raw data, and put into appropriately shaped nddata (whether
   Bruker or Spincore) → most up to date is in the processing code
   associated with ODNP aquisition, which currently lives in
   ``run_Hahn_echo_mw.py`` in ``spincore_apps/SpinCore_pp``

-  Convert short spin echoes into appropriately sliced and phased FIDs
   → most up to date in ``proc_echo_mw.py``

-  Integrate and phase the integrals → most up to date in ``proc_IR.py``

-  Fit the integrals with a relevant curve → Sam's version of
   ``proc_echo_mw.py``

-  Any potentially reusable code in the Q test code → ``proc_square_refl.py``

Top level
=========

Finally, we will construct higher-level functions, all
in a single module, that utilize these to

.. automodule:: toplevel

