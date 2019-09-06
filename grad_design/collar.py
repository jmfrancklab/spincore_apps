from solid import * # clone SolidPython from jmfrancklab repo
from solid.utils import *
id = 1
thickness = 1.5 # thickness of collar piece
width = 8 # width of collar piece
height = 4 # height of collar piece
nut_r = 0.5
screw_r = 0.3
nut_thick = 0.25
d = cylinder(r=thickness+id,h=height, center=True) + cube([thickness,width,height], center=True)
d -= cylinder(r=id,h=height*1.1, center=True)
oints = []
for theta in range(6):
    x = nut_r*cos(2*pi*theta/5.0)
    y = nut_r*sin(2*pi*theta/5.0)
    points.append([x,y])
nut_y = (thickness+id) + (width/2-thickness-id)/2
for this_pos in [-nut_y,nut_y]:
    nut = extrude_along_path(points,
            [[thickness/2-nut_thick,this_pos,0],[thickness/2+nut_thick,this_pos,0]])
    d -= nut
    d -= translate([-thickness/2,this_pos,0])(
            rotate(a=[0,90,0])(cylinder(r=screw_r, h=thickness+id+0.2)))
d['rtrans'] = 5
a = scad_render(d, file_header='$fa=5;$fs=0.1;')
with open('collar.scad','w') as fp:
    fp.write(a)
