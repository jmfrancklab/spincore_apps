from solid import *
from solid.utils import *
# units of mm
thickness = 3.0
width = 60.0
height = 127.60

d = cube([thickness,width,height], center=True)

a = scad_render(d, file_header='$fa=5;$fs=0.1;')
with open('practice.scad','w') as fp:
    fp.write(a)
