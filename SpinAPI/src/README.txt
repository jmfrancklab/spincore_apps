SpinAPI Source Code

SpinCore Technologies, Inc.
www.spincore.com

I. Introduction
===============

This directory contains the source code files used to build the SpinAPI control
library. This source code is provided for advanced users who need to port this
library to other operating systems, or who wish to understand how it works.

Users who simply need to USE the SpinAPI library can make use of the pre-compiled
version and can ignore the contents of this directory entirely. Instructions
for compiling to programs that make use of the SpinAPI library can be found in
the top-level SpinAPI directory.

Modified versions of SpinAPI cannot be officially supported, however we 
would be happy to integrate any useful modifications or enhancements into the
official source distribution.
 
Use of this source code is subject to the terms set out in the license below
in part IV.


II. Building SpinAPI from source:
=================================

The provided Makefile and Makefile.64 will build a windows .dll for SpinAPI. It is probably
somewhat specific to our internal build system, so some modifications may
be necessary depending on the compiler being used.

Makefile.linux can be used on GNU/Linux systems to generate a static SpinAPI library.

In addition to these files, an OS specific file called driver-xxx.c 
and driver-usb-xxx.c (where xxx is the name of an OS) is needed to provide
OS-specific functions.

On Windows, this is the precompiled library libdriver-windows.a. This uses
3rd party software from Jungo Ltd. to access PCI hardware. Unfortunately, the
source for libdriver-windows.a contains proprietary code so the source
cannot be released.


III. Porting SpinAPI to other Operating Systems:
================================================

The SpinAPI code itself should be fairly portable. To make SpinAPI usable on
a specific OS, driver-xxx.c and driver-usb-xxx.c files must be created to provide the
OS specific parts. driver-stub.c and driver-usb-stub are templates for those files with a 
description of what each function needs to do. To port SpinAPI to any given
OS, simply implement those driver files for that OS and link it with the
main files listed in part II above.
