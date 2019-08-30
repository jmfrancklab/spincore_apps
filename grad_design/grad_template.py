from solid import *
from solid.utils import *

# units of mm

thickness = 3.0 # hereafter t
width = 60.0 # hereafter w
height = 127.60 # hereafter h


def prism_2(l,w,h):
    return polyhedron(
            points=[[0,0,0],[l,0,0],[l,w,0],[0,w,0],[0,w,h],[l,w,h]],
            faces=[[0,1,2,3],[5,4,3,2],[0,4,5,1],[0,3,4],[5,2,1]]
            )

def prism(l,w,h):
    return polyhedron(
            points=[
                [0,0,0],[l,0,0],[0,w,0],
                [0,w,h],[l,0,h],[0,0,h]],
            faces=[[0,2,1],
                [1,0,5,4],
                [4,5,3],
                [3,4,1,2],
                [2,3,4,0]
                ]
#            faces=[[2,3,4,1],
#                   [5,4,1,0],
#                   [0,5,3,2],
#                   [0,1,2],
#                   [4,3,5]]
            )
d = cube([thickness,width,height], center=True)

arm1_t = 26.0
arm1_w = 11.0
arm1_h = 12.0
arm1 = back((width-arm1_w)/2.0)(
        right((arm1_t+thickness)/2.0)(
        cube([arm1_t,arm1_w,arm1_h], center=True)))
      
arm2_t = 4.0
arm2_w = 10.0
arm2_h = 12.0
arm2 = back((arm2_w+width)/2.0)(
        right(-arm2_t+arm1_t+(arm2_t+thickness)/2.0)(
        cube([arm2_t,arm2_w,arm2_h],center=True)))
d += arm1 + arm2

prism_t = 2.32
prism_w = 4.0
prism_h = 12.0

path_offset_h = 8.90
path_offset_w = arm1_w + prism_w
print path_offset_w

path1_t = 3.0
path1_w = 42.55
path1_h = 2.55
path1 = right(thickness/2.0)(
        back((-path1_w+width)/2.0-path_offset_w-0.01)(
        up((-path1_h+height)/2.0 - path_offset_h)(
            cube([path1_t,path1_w,path1_h],center=True))))
path2_t = 3.0
path2_w = 2.55
path2_h = 109.8
path2 = back((-path2_w+width)/2.0-path_offset_w-0.01)(
        right(thickness/2.0)(
            cube([path2_t,path2_w,path2_h],center=True)))
            
path3_t = 3.0
path3_w = 2.55
path3_h = 41.3
path3 = back((-path3_w+width)/2.0-path_offset_w-0.01-path1_w+path3_w)(
        right(thickness/2.0)(
                up((-path3_h+height)/2.0 - path_offset_h)(
                cube([path3_t,path3_w,path3_h],center=True))))

path4_t = 3.0
path4_w = 42.55+path_offset_w+0.01
path4_h = 2.55
path4 = right(thickness/2.0)(
        back((-path4_w+width)/2.0)(
            up((-path4_h+height)/2.0 - path_offset_h - path3_h + path4_h)(
                cube([path4_t,path4_w,path4_h],center=True))))

path5_t = 3.0
path5_w = 42.55
path5_h = 2.55
path5 = right(thickness/2.0)(
        back((-path5_w+width)/2.0-path_offset_w-0.01)(
                down((-path5_h+height)/2.0 - path_offset_h)(
                    cube([path5_t,path5_w,path5_h],center=True))))

path6_t = 3.0
path6_w = 2.55
path6_h = 41.3
path6 = back((-path6_w+width)/2.0-path_offset_w-0.01-path1_w+path6_w)(
        right(thickness/2.0)(
            down((-path6_h+height)/2.0 - path_offset_h)(
                cube([path6_t,path6_w,path6_h],center=True))))

path7_t = 3.0
path7_w = 42.55
path7_h = 2.55
path7 = back((-path7_w+width)/2.0-path_offset_w-0.01)(
        right(thickness/2.0)(
            down((-path7_h+height)/2.0 - path_offset_h - path3_h + path7_h)(
            cube([path7_t,path7_w,path7_h],center=True))))

all_paths = [path1,path2,path3,
        path4,path5,path6,path7]
for this_path in all_paths:
    d += hole()(this_path)


d += down(prism_h/2.0)(
        right(thickness/2.0)(
            back(width/2.0-arm1_w)(
    prism_2(prism_t,prism_w,prism_h))))

a = scad_render(d, file_header='$fa=5;$fs=0.01;')
with open('grad_temp.scad','w') as fp:
    fp.write(a)
