#!/bin/sh
# tkp 111307
# SpinCore Technologies, Inc. 
# Latest Modifications: December 07, 2009 by Chris Hett
# Special thanks to Tom Prattum, Western Washington University
# This script uses incl_160.exe, incl_250.exe, incl_300.exe, incl_500.exe, incl_3200.exe programs 
# to control the PTS frequency synthesizers.
# Check back at SpinCore.com for future software developements. 
# It is assumed that the incl executables are in the includes sub-directory of the location of the script

# exec wish "$0" "$@"; # starts the windowing shell - use for Mac systems
wm title . {www.spincore.com}

global textMHz textPhase runcmd1 textCommand1 retmsg1 device

# these lines set the default values shown in the textboxes
set textMHz {1.0}
set textPhase {0}

global textFStart textFEnd textdF textPhase1 textDelay

# these lines set the default values shown in the textboxes and radio buttons
set textFStart {5.0}
set textFEnd {20.0}
set textdF {0.5}
set textPhase1 {0}
set textDelay {100}
set device PTS250

# the next commands set the window up
frame .f
frame .f0
frame .f1
frame .f2
frame .f3
frame .f4
frame .f5
frame .f6
frame .f7
frame .f8
frame .f9
frame .f10
frame .f11
frame .f12
frame .f13

label .l -font *-arial-bold-r-normal--18-*-*-*-*-*-*-* -fg #660000 -text "SpinCore USB-PTS Controller"
label .l1 -text "Frequency (MHz):"
entry .e1 -width 20 -relief sunken -bd 1 -textvariable textMHz
label .l2 -text "Phase (deg):"
entry .e2 -width 4 -relief sunken -bd 1 -textvariable textPhase
message .m1 -font *-arial-medium-normal--14-*-*-*-*-*-*-* -fg #006600 -width 6c -textvariable retmsg1

label .l4 -font *-arial-bold-r-normal--16-*-*-*-*-*-*-* -fg #000000 -text "Frequency Sweep Generation"
label .l5 -text "Starting Frequency (MHz):"
entry .e5 -width 20 -relief sunken -bd 1 -textvariable textFStart
label .l6 -text "Ending Frequency (MHz):"
entry .e6 -width 20 -relief sunken -bd 1 -textvariable textFEnd
label .l7 -text "Increment (MHz):"
entry .e7 -width 20 -relief sunken -bd 1 -textvariable textdF
label .l8 -text "Phase (Degrees):"
entry .e8 -width 20 -relief sunken -bd 1 -textvariable textPhase1
label .l9 -text "Delay (ms):"
entry .e9 -width 20 -relief sunken -bd 1 -textvariable textDelay
label .l10 -font *-arial-bold-r-normal--16-*-*-*-*-*-*-* -fg #000000 -text "Single Frequency Generation"
label .l11 -text " "
button .a -text "Set Synthesizer" -command "putsVars"

pack .f -side top -padx 3m -pady 3m
pack .l -side top -pady 5 -in .f
pack .l10 -side top -in .f1
pack .f0 -side top -pady 4m -in .f
pack .f1 -side top -padx 3m -in .f
pack .f2 -side top -padx 3m -in .f
pack .l1 .e1 -side left -pady 1m -in .f1 
pack .a -side left -padx 2m -in .f1 
pack .l2 .e2 -side left -in .f2 
pack .f3 -side top -padx 3m -pady 1m -in .f
pack .f4 -side top -padx 3m -in .f
pack .f5 -side top -padx 1m -in .f
pack .f6 -side top -padx 3m -in .f

pack .l11 -side top -in .f
pack .l4 -side top -in .f
pack .f7 -side top -padx 3m -in .f
pack .f8 -side top -padx 3m -in .f
pack .f9 -side top -padx 3m -in .f
pack .f10 -side top -padx 3m -in .f
pack .f11 -side top -padx 3m -in .f
pack .f12 -side top -padx 3m -in .f
pack .f13 -side top -padx 3m -in .f
pack .l5 .e5 -side left -pady 1m -in .f7 
pack .l6 .e6 -side left -pady 1m -in .f8 
pack .l7 .e7 -side left -pady 1m -in .f9 
pack .l8 .e8 -side left -pady 1m -in .f10 
pack .l9 .e9 -side left -pady 1m -in .f11 

button .but_vfu -text "+5.0" -command "veryfastUp"
button .but_vfd -text "-5.0" -command "veryfastDown"
button .but_fu -text "+1.0" -command "fastUp"
button .but_fd -text "-1.0" -command "fastDown"
button .but_su -text "+0.1" -command "slowUp"
button .but_sd -text "-0.1" -command "slowDown"
bind all <KP_Add> {fastUp}
pack .but_vfd .but_fd .but_sd .but_su .but_fu .but_vfu -side left -in .f4
pack .m1 -in .f13
button .a1 -text "Run Sweep" -command "putsSweepOnce"
pack .a1 -side top -in .f12

radiobutton .rad1 -text "PTS160" -variable device -value PTS160 
radiobutton .rad2 -text "PTS250" -variable device -value PTS250 
radiobutton .rad3 -text "PTS300" -variable device -value PTS300 
radiobutton .rad4 -text "PTS500" -variable device -value PTS500 
radiobutton .rad5 -text "PTS3200" -variable device -value PTS3200 
pack .rad1 .rad2 .rad3 .rad4 .rad5 -side left -in .f0

# procedure for generating the command from the variables entered
proc putsVars {} {
	global textMHz textPhase runcmd1 textCommand1 retmsg1 device
	switch -- $device {
		PTS160 {
			set runcmd1 [list exec [file join [pwd] ./includes/incl_160.exe] $textMHz]
		}
		PTS250 {
			set runcmd1 [list exec [file join [pwd] ./includes/incl_250.exe] $textMHz]
		}
		PTS300 {
			set runcmd1 [list exec [file join [pwd] ./includes/incl_300.exe] $textMHz $textPhase]
		}
		PTS500 {
			set runcmd1 [list exec [file join [pwd] ./includes/incl_500.exe] $textMHz]
		}
		PTS3200 {
			set runcmd1 [list exec [file join [pwd] ./includes/incl_3200.exe] $textMHz]
		}
		default {}
	}
	eval catch {$runcmd1} retmsg1
}


proc putsSweepOnce {} {
	global textFStart textFEnd textdF textPhase1 textDelay runcmd1 textCommand1 retmsg1 device
	switch -- $device {
		PTS160 {
			set runcmd1 [list exec [file join [pwd] ./includes/incl_fsweep_once_160.exe] $textFStart $textFEnd $textdF $textPhase1 $textDelay]
		}
		PTS250 {
			set runcmd1 [list exec [file join [pwd] ./includes/incl_fsweep_once_250.exe] $textFStart $textFEnd $textdF $textPhase1 $textDelay]
		}
		PTS300 {
			set runcmd1 [list exec [file join [pwd] ./includes/incl_fsweep_once_300.exe] $textFStart $textFEnd $textdF $textPhase1 $textDelay]
		}
		PTS500 {
			set runcmd1 [list exec [file join [pwd] ./includes/incl_fsweep_once_500.exe] $textFStart $textFEnd $textdF $textPhase1 $textDelay]
		}
		PTS3200 {
			set runcmd1 [list exec [file join [pwd] ./includes/incl_fsweep_once_3200.exe] $textFStart $textFEnd $textdF $textPhase1 $textDelay]
		}
	}		
	eval catch {$runcmd1} retmsg1
}

# procedure for generating the command from the variables entered
proc veryfastUp {} {
	global textMHz textPhase runcmd1 textCommand1 retmsg1 device
		set textMHz [expr $textMHz + 5.0]
		updateValue
}

proc veryfastDown {} {
	global textMHz textPhase runcmd1 textCommand1 retmsg1 device
	if { $textMHz > 5.0 } {
		set textMHz [expr $textMHz - 5.0]
		updateValue
	}
}

proc fastUp {} {
	global textMHz textPhase runcmd1 textCommand1 retmsg1 device
		set textMHz [expr $textMHz + 1.0]
		updateValue
}

proc fastDown {} {
	global textMHz textPhase runcmd1 textCommand1 retmsg1 device
	if { $textMHz > 1.0 } {
		set textMHz [expr $textMHz - 1.0]
		updateValue
	}
}

proc slowUp {} {
	global textMHz textPhase runcmd1 textCommand1 retmsg1 device
		set textMHz [expr (($textMHz)*10 + 1)/10]
		updateValue
}

proc slowDown {} {
	global textMHz textPhase runcmd1 textCommand1 retmsg1 device
		if { $textMHz > 0.1 } {
			set textMHz [expr (($textMHz)*10 - 1)/10]
			updateValue
		}
}

proc updateValue {} {
	global textMHz textPhase runcmd1 textCommand1 retmsg1 device
	switch -- $device {
		PTS160 {
			set runcmd1 [list exec [file join [pwd] ./includes/incl_160.exe] $textMHz]
		}
		PTS250 {
			set runcmd1 [list exec [file join [pwd] ./includes/incl_250.exe] $textMHz]
		}
		PTS300 {
			set runcmd1 [list exec [file join [pwd] ./includes/incl_300.exe] $textMHz $textPhase]
		}
		PTS500 {
			set runcmd1 [list exec [file join [pwd] ./includes/incl_500.exe] $textMHz]
		}
		PTS3200 {
			set runcmd1 [list exec [file join [pwd] ./includes/incl_3200.exe] $textMHz]
		}
		default {}
	}
	eval catch {$runcmd1} retmsg1
	#.m1 configure -text "$textMHz"
}