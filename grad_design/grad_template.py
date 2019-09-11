from solid import *
from solid.utils import *

# units of mm

thickness = 3.0 # hereafter t
width = 78.0 # hereafter w
height = 127.60 # hereafter h

#{{{ all this is used just to generate a right triangular prism
def prism_2(l,w,h):
    return polyhedron(
            points=[[0,0,0],[l,0,0],[l,w,0],[0,w,0],[0,w,h],[l,w,h]],
            faces=[[0,1,2,3],[5,4,3,2],[0,4,5,1],[0,3,4],[5,2,1]]
            )
def prism_3(l,w,h):
    # taking prism_2 and rotating it
    return polyhedron(
            points=[[0,0,0],[0,0,l],[0,w,l],[0,w,0],[h,w,0],[h,w,l]],
            faces=[[0,1,2,3],[5,4,3,2],[0,4,5,1],[0,3,4],[5,2,1]]
            )
#}}}


prism_t = 12.0 # this becomes the height
prism_w = 4.0
prism_h = 2.32 # this becomes the thickness
    #{{{
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

arm3_t = 26.00 
arm3_w = 8.00
arm3_h = 12.0
arm3 = back((-width+arm3_w)/2.0)(
        right((arm3_t+thickness)/2.0)(
            up((90.-height/2.)+arm3_h/2.)(
                cube([arm3_t,arm3_w,arm3_h], center=True))))

arm4_t = 4.0
arm4_w = 10.0
arm4_h = 12.0
arm4 = back((-width-arm4_w)/2.0)(
        right(-arm4_t+arm3_t+(arm4_t+thickness)/2.0)(
            up((90.-height/2.)+arm4_h/2.)(
            cube([arm4_t,arm4_w,arm4_h],center=True))))

d += arm1 + arm2 + arm3 + arm4

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
print (-path6_w+width)/2.0 - path_offset_w-0.01 - path1_w + path6_w

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

d += back(width/2.0-arm1_w-prism_w)(
        right(thickness/2.0)(
        down(prism_t/2.0)(
        (prism_3(prism_t,-1*prism_w,prism_h)))))

# this will make a nut hole with points defined
# in the x plane, so it is a hole in the x plan
# whose position can be manipulated by altering
# the x,y,z variables in extrude_along_path
nut_radius = 2.1844
nut_thickness = 100.0

points = []
for theta in xrange(6):
    x = nut_radius*cos(2*pi*theta/6.0)
    y = nut_radius*sin(2*pi*theta/6.0)
    points.append([x,y])
nut1_width = (width+arm2_w)/2.
nut1 = extrude_along_path(points,
        [[-nut_thickness,-nut1_width,0],
            [nut_thickness,-nut1_width,0]])
nut2_width = (width+arm4_w)/2.
nut2_height = (90.-height/2.0)+arm4_h/2.
nut2 = extrude_along_path(points,
        [[-nut_thickness,nut2_width,nut2_height],
            [nut_thickness,nut2_width,nut2_height]])

all_nuts = [nut1,nut2]
for this_nut in all_nuts:
    d += hole()(this_nut)

a = scad_render(d, file_header='$fa=5;$fs=0.01;')
with open('grad_temp.scad','w') as fp:
    fp.write(a)
