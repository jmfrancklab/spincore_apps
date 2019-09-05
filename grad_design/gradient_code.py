from pyspecdata import *
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import interp1d
from math import atan2
clf()
ax = subplot(111, projection='3d')

length = 4.0e-2
Z0 = 2.5e-2
width = 1.55*Z0
y_c = 1.19*Z0

def stack_cart(x,y,z):
    if isscalar(y):
        y = y*ones_like(z)
        x = x*ones_like(z)
    elif isscalar(z):
        z = z*ones_like(y)
        x = x*ones_like(y)
    return stack((x,y,z)).T

class path_obj(object):
    def __init__(self,x,y,z):
        self.current_path = stack_cart(x,y,z)
        return
    def addpath(self,x,y,z):
        p = stack_cart(x,y,z)
        self.current_path = concatenate((self.current_path,p))
    def __add__(self,pathtuple):
        assert len(pathtuple)==3
        self.addpath(*pathtuple)
        return self
    def plot(self):
        ax.plot(*[self.current_path[:,j] for j in xrange(3)],
                color='k')
        return
    def small_pieces(self,piece_length=0.01e-3):
        print "Printing current path..."
        print self.current_path
        dl = diff(self.current_path,axis=0)
        print "Printing dl"
        print dl
        dl_size = sqrt((dl**2).sum(axis=1))
        print "Printing dl_size..."
        print dl_size
        dl_size = r_[0,dl_size]
        print "Printing new dl_size..."
        print dl_size
        progress_along_length = cumsum(dl_size)
        print "Printing progress_along_length..."
        print progress_along_length

        print "*** *** ***"
        print "LENGTH OF WIRE:",progress_along_length[-1]
        print "WAS INPUT IN",len(progress_along_length),"PIECES"
        print "BEGINNING TO INTERPOLATE..."
        x_coords = interp1d(
                progress_along_length,self.current_path[:,0],
                kind='linear')
        y_coords = interp1d(
                progress_along_length,self.current_path[:,1],
                kind='linear')
        z_coords = interp1d(
                progress_along_length,self.current_path[:,2],
                kind='linear')
        new_progress = r_[0:
                progress_along_length[-1]:
                piece_length]
        print "DIVIDING INTO",len(new_progress),"PIECES"
        self.current_path = stack((
            x_coords(new_progress),
            y_coords(new_progress),
            z_coords(new_progress))).T
        self.is_smooth = True
        return self
    def calculate_biot(self,grid,threshold=1e-3):
        print "ENTERING CALCULATE_BIOT FUNCTION..."
        assert hasattr(self,'is_smooth') and self.is_smooth, "you must smooth before running biot-savart"
        dl = diff(self.current_path,axis=0)
        centerpoint = (self.current_path[:-1,:]
                +self.current_path[1:,:])/2
        dl = dl[newaxis,:,:]
        grid = grid[:,newaxis,:]
        centerpoint = centerpoint[newaxis,:,:]
        rprime = grid-centerpoint
        rprime_len = sqrt((rprime**2
            ).sum(axis=-1,keepdims=True))
        if threshold != None:
            rprime_len[rprime_len < threshold] = nan
        print shape(rprime)
        print shape(rprime_len)
        retval = mu_0/4/pi*(cross(dl,rprime)/rprime_len**3).sum(axis=1)
        print "EXITING CALCULATE_BIOT FUNCTION..."
        return retval
cable = -1*(length/2.+length/4.)
p1 = path_obj(Z0, 
        r_[cable,-length/2],

        y_c/2) # input wire for RF connector
p1 += (Z0,
        r_[-length/2,length/2],
        y_c/2)
p1 += (Z0,
        length/2,
        r_[y_c/2, width+y_c/2])
p1 += (Z0,
        r_[length/2,-length/2],
        width+y_c/2)
p1 += (Z0,
        -length/2,
        r_[width+y_c/2,y_c/2])
p1 += (Z0,
        -length/2,
        r_[y_c/2,-y_c/2]) # connects top loop to bottom
p1 += (Z0,
        r_[-length/2,length/2],
        -1*y_c/2)
p1 += (Z0,
        length/2,
        -1*r_[y_c/2, width+y_c/2])
p1 += (Z0,
        r_[length/2,-length/2],
        -1*(width+y_c/2))
p1 += (Z0,
        -length/2,
        r_[-1*(width+y_c/2),-y_c/2])
p1 += (Z0,
        -length/2,
        r_[-y_c/2,y_c/2]) # connects bottom loop to top
p1 += (Z0,
        r_[-length/2,cable],
        y_c/2) # output for RF connector
p1.small_pieces()
p1.plot()

#x_points = r_[-Z0,0,Z0]
#x_points = r_[0:Z0:16j]
x_points = r_[Z0]
y_points = r_[-length/2.,-length/4.,0,length/4.,length/2.]
z_points = r_[-1*(y_c+width):y_c+width:49j]
ones_grid = ones((len(x_points),
    len(y_points),
    len(z_points)))
x_points = x_points[:,newaxis,newaxis]
y_points = y_points[newaxis,:,newaxis]
z_points = z_points[newaxis,newaxis,:]

point_grid = stack((
    x_points*ones_grid,
    y_points*ones_grid,
    z_points*ones_grid)).transpose(
            (1,2,3,0)
            ).reshape((-1,3))

fields = p1.calculate_biot(point_grid) #+ p2.calculate_biot(point_grid)
print "***"
print shape(fields)
print shape(point_grid)
print "***"
fields_asgrid = fields.reshape(x_points.size,y_points.size,z_points.size,3)
point_grid_ = point_grid.reshape(x_points.size,y_points.size,z_points.size,3)
#{{{ The following is for determining the partial area, as discussed in Volkmar
#et al. 2013, however given that we use an equally spaced grid of x,y,z points,
#all the work I am doing is highly redundant, because the objective is to
#calculate the area defined by the mesh grid into which the B vector enters
#(perpendicularly), and due to the evenly spaced grid, the area defined by the
#mesh is constant and unchanging. Thus it suffices to determine simply the
#difference between any two y points and any two z points, for example, and then
#calculate the area from those differences, and then this area would be used for
#the remainder of the problem (i.e., eq 13 in Volkmar et al. 2013)
y_halfpoints = (point_grid_[:,:-1,:,:] + point_grid_[:,1:,:,:]) / 2.
z_halfpoints = (point_grid_[:,:,:-1,:] + point_grid_[:,:,1:,:]) / 2.
y_diff = y_halfpoints[:,:,:,:]-point_grid_[:,:-1,:,:]
z_diff = z_halfpoints[:,:,:,:]-point_grid_[:,:,:-1,:]
dA = y_diff[0,0,0,1]*z_diff[0,0,0,-1]
#}}}
fields_nothresh = p1.calculate_biot(point_grid,threshold=None)
fields_nothresh_grid = fields_nothresh.reshape(x_points.size,
        y_points.size,z_points.size,3)
fields_normal = fields_nothresh_grid[:,:,:,0]
fields_normal *= dA
fields_normal[isnan(fields_normal)] = 0
flux = (fields_normal.sum(axis=2)).sum(axis=1)[0]
print "*** *** ***"
print "Calculated self-inductance =",flux
print "*** *** ***"
figure(1)
ax.quiver(*(
    [point_grid[:,j] for j in xrange(3)]
    +[500*fields[:,j] for j in xrange(3)]
    ),
    pivot = 'middle')
figure(2)
title('Field Map, vertical cavity slice')
y_2d = y_points[0,:,:]
z_2d = z_points[0,:,:]
print "Y-axis starts at",y_points[0,0,0]
print "Z-axis starts at",z_points[0,0,0]
contourf(y_2d*ones_like(z_2d)/1e-3, # grid providing the y-axis dimensions
        z_2d*ones_like(y_2d)/1e-3, # grid providing the z-axis dimensions
        fields_asgrid[0,:,:,0], # grid of the field as a function of y,z
        100)
xlabel(r'x axis (in plane of and normal to $B_0$) / mm')
ylabel(r'z axis (upward, lab frame) / mm')
colorbar()
figure(3)
y_index = int(0.5*fields_asgrid.shape[1]+0.5)
plot(z_points[0,0,:]/1e-3, # grid of the z-axis dimensions
        fields_asgrid[0,y_index,:,0]/1e-6, # grid of the field as a function of z (taken through central y)
        'k')
xlabel(r'position / mm')
ylabel(r'field / $\mu$T A$^{-1}$')


show()
