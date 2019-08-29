from solid import *
from solid.utils import *

# units of mm

thickness = 3.0
width = 60.0
height = 127.60

d = cube([thickness,width,height], center=True)

arm1 = right(thickness/2.0)(down(12.0/2.0)(back(30.0)(
            cube([26.0,11.0,12.0]))))
arm2 = right(-4.0 + 26.0 + thickness/2.0)(down(12.0/2.0)(back(30.0+10.0)(
            cube([4.0,10.0,12.0]))))
path1 = back(-8.725 + width/2.0)(up(height/2.0 - 8.725)(
            cube([1.5,42.55,2.55])))
path2 = down(-2.55+109.8/2.)(back(-8.725 + width/2.0)(
            cube([1.5,2.55,109.8])))
d += arm1 + arm2
all_paths = [path1,path2]
for this_path in all_paths:
    d += hole()(this_path)
a = scad_render(d, file_header='$fa=5;$fs=0.1;')
with open('grad_temp.scad','w') as fp:
    fp.write(a)
