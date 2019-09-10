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

degrees_to_radians = pi/180.

def cyl_to_cart(r,theta,z):
    if isscalar(z):
        z = z*ones_like(theta)
    elif isscalar(theta):
        theta = theta*ones_like(z)
    return stack((r*cos(theta*degrees_to_radians),
        r*sin(theta*degrees_to_radians),
        z)).T

def stack_cart(x,y,z):
    if isscalar(y):
        y = y*ones_like(z)
        x = x*ones_like(z)
    elif isscalar(z):
        z = z*ones_like(y)
        x = x*ones_like(y)
    return stack((x,y,z)).T

#{{{ class object for constructions specified in cylindrical coordinates
class path_obj_cyl(object):
    def __init__(self,r,theta,z):
        self.current_path = cyl_to_cart(r,theta,z)
        return
    def addpath(self,r,theta,z):
        p = cyl_to_cart(r,theta,z)
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
        print shape(self.current_path)
        dl = diff(self.current_path,axis=0)
        print "Printing dl"
        print shape(dl)
        dl_size = sqrt((dl**2).sum(axis=1))
        print shape(dl_size)
        print "Printing dl_size..."
        dl_size = r_[0,dl_size]
        print "Printing new dl_size..."
        progress_along_length = cumsum(dl_size)
        print "Printing progress_along_length..."
        print shape(progress_along_length)
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
#}}}

#{{{ class object for constructions described by Cartesian coordinates
class path_obj_cart(object):
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
        dl = diff(self.current_path,axis=0)
        dl_size = sqrt((dl**2).sum(axis=1))
        dl_size = r_[0,dl_size]
        progress_along_length = cumsum(dl_size)
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
#}}}

#{{{ defining solenoid
# Note that for the simulation to compare well against the simple formula, we
# need to define a very small solenoid like so
solenoid_r = 0.1
solenoid_l = 0.5
n_turns = 8

p1 = path_obj_cyl(solenoid_r,
        r_[-360:360*n_turns:1000j],
        r_[-solenoid_l/2:solenoid_l/2:1000j])
#}}}
p1.small_pieces()
p1.plot()

x_points = r_[-0.3:0.3:5j]
y_points = r_[-0.3:0.3:5j]
z_points = r_[-solenoid_l:solenoid_l:5j]

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

fields = p1.calculate_biot(point_grid)# + p2.calculate_biot(point_grid)
calculate_magnitude = False
if calculate_magnitude:
    field_mag = sqrt((fields**2).sum(axis=-1))
    print "*** BIOT-SAVART SIMULATION ***"
    print "Magnitude of magnetic field in center:",field_mag[0],"T"
    print "*** EMPIRICAL FORMULA ***"
    print "Magnitude of magnetic field in center:",(mu_0*n_turns),"T"
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
#}}}
#{{{ calculating self-inductance
self_inductance = False
if self_inductance:
    y_halfpoints = (point_grid_[:,:-1,:,:] + point_grid_[:,1:,:,:]) / 2.
    z_halfpoints = (point_grid_[:,:,:-1,:] + point_grid_[:,:,1:,:]) / 2.
    y_diff = y_halfpoints[:,:,:,:]-point_grid_[:,:-1,:,:]
    z_diff = z_halfpoints[:,:,:,:]-point_grid_[:,:,:-1,:]
    dA = y_diff[0,0,0,1]*z_diff[0,0,0,-1]
    fields_nothresh = p1.calculate_biot(point_grid,threshold=None)
    fields_nothresh_grid = fields_nothresh.reshape(x_points.size,
            y_points.size,z_points.size,3)
    fields_normal = fields_nothresh_grid[:,:,:,0]
    fields_normal *= dA
    fields_normal[isnan(fields_normal)] = 0
    flux = (fields_normal.sum(axis=2)).sum(axis=1)[0]
    print "*** *** ***"
    print "CALCULATED SELF INDUCTANCE AS",abs(flux),"HENRIES / AMPERE"
    print "*** *** ***"
#}}}
#figure(1)
#ax.quiver(*(
#    [point_grid[:,j] for j in xrange(3)]
#    +[500*fields[:,j] for j in xrange(3)]
#    ),
#    pivot = 'middle')
figure(2)
title('Field Map: xy plane, z component')
y_2d = y_points[:,:,0]
x_2d = x_points[:,:,0]
contourf(y_2d*ones_like(x_2d)/1e-3, # grid providing the y-axis dimensions
        x_2d*ones_like(y_2d)/1e-3, # grid providing the z-axis dimensions
        fields_asgrid[:,:,0,2], # grid of the field as a function of y,z
        100)
xlabel(r'y axis / mm')
ylabel(r'x axis / mm')
colorbar()
x_halfpoints = (point_grid_[:-1,:,:,:] + point_grid_[1:,:,:,:]) / 2.
y_halfpoints = (point_grid_[:,:-1,:,:] + point_grid_[:,1:,:,:]) / 2.
z_halfpoints = (point_grid_[:,:,:-1,:] + point_grid_[:,:,1:,:]) / 2.
x_diff = x_halfpoints[:,:,:,:] - point_grid_[:-1,:,:,:]
y_diff = y_halfpoints[:,:,:,:] - point_grid_[:,:-1,:,:]
z_diff = z_halfpoints[:,:,:,:] - point_grid_[:,:,:-1,:]
print shape(x_diff)
print shape(y_diff)
print shape(z_diff)
dV = x_diff[0,0,0,0]*y_diff[0,0,0,1]*z_diff[0,0,0,-1]
fields_nothresh = p1.calculate_biot(point_grid,threshold=None)
fields_nothresh_grid = fields_nothresh.reshape(x_points.size,
        y_points.size,z_points.size,3)
fields_nothresh_grid *= fields_nothresh_grid
fields_nothresh_grid *= dV*2*mu_0
inductance = ((fields_nothresh_grid.sum(axis=-1)).sum(axis=1)).sum(axis=0)
inductance = sqrt( inductance[0]**2 + inductance[1]**2 + inductance[2]**2 )
print inductance
quit()



#fields_mag = sqrt((fields_nothresh_grid[:,:,:,0])**2 + (fields_nothresh_grid[:,:,:,1])**2 + (fields_nothresh_grid[:,:,:,-1])**2)
fields_nothresh_grid[isnan(fields_nothresh_grid)] = 0
#fields_mag[isnan(fields_mag)] = 0
fields_mag = fields_nothresh_grid**2 * dV * 2 * mu_0
#fields_mag *= fields_mag
#fields_mag *= dV*2*mu_0
inductance = ((fields_mag.sum(axis=2)).sum(axis=1)).sum(axis=0)
inductance = sqrt((inductance[0]**2 + inductance[1]**2 + inductance[2]**2 ))
print shape(inductance)
print inductance
quit()
show();quit()
figure(3)
y_index = int(0.5*fields_asgrid.shape[1]+0.5)
plot(z_points[0,0,:]/1e-3, # grid of the z-axis dimensions
        fields_asgrid[0,y_index,:,0]/1e-6, # grid of the field as a function of z (taken through central y)
        'k')
xlabel(r'position / mm')
ylabel(r'field / $\mu$T A$^{-1}$')


show()
