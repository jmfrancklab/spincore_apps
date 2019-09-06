from solid import *
from solid.utils import *


nut_radius = 10.0
screw_radius = 10.0
nut_thickness = 10.0

points = []
for theta in xrange(6):
    x = nut_radius*cos(2*pi*theta/6.0)
    y = nut_radius*sin(2*pi*theta/6.0)
    points.append([x,y])
nut_y = 0.0
for this_pos in [-nut_y,nut_y]:
    nut = extrude_along_path(points,
            [[-nut_thickness,this_pos,0],[nut_thickness,this_pos,0]])
d = nut

a = scad_render(d, file_header='$fa=5;$fs=0.01;')
with open('test_nut.scad','w') as fp:
    fp.write(a)
