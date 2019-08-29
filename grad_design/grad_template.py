from solid import *
from solid.utils import *

#def prism(l,w,h):
#    z = 0.08
#    separation = 2
#    border = 0.2
#    polyhedron(
#        points = [[0,0,0],[1,0,0],[l,w,0],[0,w,0],[0,w,h],[l,w,h]],
#        faces = [[0,1,2,3],[5,4,3,2],[0,4,5,1],[0,3,4],[5,2,1]]
#        )
#    left(w+separation)(cube([l,w,z]))
#    left(w+separation+w+border)(cube([l,sqrt(w*w+h*h),z]))
#    left(w+separation+w+border+h+border)(cube([l,sqrt(w*w+h*h),z]))
#    up(l+border)(left(w+separation+w+border+h+border)(
#        polyhedron(
#            points=[[0,0,0],[0-h,0,0],[0,sqrt(w*w*+h*h),0],[0,0,z],[0-h,0,z],
#            [0,sqrt(w*w+h*h),z]],
#        faces=[[1,0,2],[5,3,4],[0,1,4,3],[1,2,5,4],[2,0,3,5]]
#        )))
#    up(0-border)(left(w+separation+w+border+h+border)(
#        polyhedron(
#            points=[[0,0,0],[0-h,0,0],[0,sqrt(w*w+h*h),0],[0,0,z],[0-h,0,z],
#            [0,sqrt(w*w+h*h),z]],
#            faces=[[1,0,2],[5,3,4],[0,1,4,3],[1,2,5,4],[2,0,3,5]]
#                )))
#    return

#####l = 10.0
#####w = 5.0
#####h = 3.0
#####z = 0.08
#####separation = 2
#####border = 0.2
#####k = polyhedron(
#####    points = [[0,0,0],[1,0,0],[l,w,0],[0,w,0],[0,w,h],[l,w,h]],
#####    faces = [[0,1,2,3],[5,4,3,2],[0,4,5,1],[0,3,4],[5,2,1]]
#####    )
#####k += left(w+separation)(cube([l,w,z]))
#####k += left(w+separation+w+border)(cube([l,sqrt(w*w+h*h),z]))
#####k += left(w+separation+w+border+h+border)(cube([l,sqrt(w*w+h*h),z]))
#####k += up(l+border)(left(w+separation+w+border+h+border)(
#####    polyhedron(
#####        points=[[0,0,0],[0-h,0,0],[0,sqrt(w*w*+h*h),0],[0,0,z],[0-h,0,z],
#####        [0,sqrt(w*w+h*h),z]],
#####    faces=[[1,0,2],[5,3,4],[0,1,4,3],[1,2,5,4],[2,0,3,5]]
#####    )))
#####k += up(0-border)(left(w+separation+w+border+h+border)(
#####    polyhedron(
#####        points=[[0,0,0],[0-h,0,0],[0,sqrt(w*w+h*h),0],[0,0,z],[0-h,0,z],
#####        [0,sqrt(w*w+h*h),z]],
#####        faces=[[1,0,2],[5,3,4],[0,1,4,3],[1,2,5,4],[2,0,3,5]]
#####            )))

# units of mm
thickness = 3.0 # hereafter t
width = 60.0 # hereafter w
height = 127.60 # hereafter h

def prism(l,w,h):
    return polyhedron(
            points=[
                [0,0,0],[l,0,0],[0,w,0],
                [0,w,h],[l,0,h],[0,0,h]],
            faces=[[0,1,2],[2,3,4,1],
                   [4,3,5],[5,4,1,0],
                   [0,5,3,2]]
            )
k = prism(15,7,3)
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
