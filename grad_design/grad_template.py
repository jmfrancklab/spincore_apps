from solid import *
from solid.utils import *

# units of mm
thickness = 3.0 # hereafter t
width = 60.0 # hereafter w
height = 127.60 # hereafter h

k = polyhedron(
        points=[[0,0,0],[10,0,0],[10,7,0],[0,7,0],[0,0,5],[10,0,5],
        [10,7,5],[0,7,5]],
        faces=[[0,1,2,3],[4,5,1,0],[7,6,5,4],[5,6,2,1],[6,7,3,2],
        [7,4,0,3]])

#d = cube([thickness,width,height], center=True)
#
#arm1_t = 26.0
#arm1_w = 11.0
#arm1_h = 12.0
#arm1 = back((width-arm1_w)/2.0)(right((arm1_t+thickness)/2.0)(
#        cube([arm1_t,arm1_w,arm1_h], center=True)))
#      
#arm2_t = 4.0
#arm2_w = 10.0
#arm2_h = 12.0
#arm2 = back((arm2_w+width)/2.0)(right(-arm2_t+arm1_t+(arm2_t+thickness)/2.0)(
#        cube([arm2_t,arm2_w,arm2_h],center=True)))
#
#path1 = back(-8.725 + width/2.0)(up(height/2.0 - 8.725)(
#            cube([1.5,42.55,2.55])))
#path2 = down(-2.55+109.8/2.)(back(-8.725 + width/2.0)(
#            cube([1.5,2.55,109.8])))
#d += arm1 + arm2
#all_paths = [path1,path2]
#for this_path in all_paths:
#    d += hole()(this_path)
#a = scad_render(d, file_header='$fa=5;$fs=0.1;')
a = scad_render(k, file_header='$fa=5;$fs=0.1;')
with open('grad_temp.scad','w') as fp:
    fp.write(a)
