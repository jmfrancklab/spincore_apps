from pyspecdata import *
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import interp1d
from math import atan2
clf()
ax = subplot(111, projection='3d')

# See MRI 1992 Callaghan
length = 4.0e-2
Z0 = 2.5e-2
width = 1.55*Z0
y_c = 1.19*Z0


def cyl_to_cart(r,theta,z):
    r"""cylindrical to cartesian, using **degrees** for
    theta.
    
    Returns
    =======
    coordinates: ndarray
        (list of points)x(x,y,z)
    """
    if isscalar(z):
        # if r is a scalar, numpy will handle that
        # automatically, but we not infrequently want a
        # z that's all the same
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

# considering that you would want this for Biot-Savart
# calculations, I construct a list of coordinates,
# rather than directly plotting them, and then I plot
# them when I'm done; this way, you could take the list
# and Biot-Savart them:

# at first, I was just thinking about using the
# parametric equation for a circle,
# but then I realized it was simpler to just put things
# in terms of cylindrical coordinates

class path_obj (object):
    def __init__(self,x,y,z):
        self.current_path = stack_cart(x,y,z)
        return
    def addpath(self,x,y,z):
        p = stack_cart(x,y,z)
        self.current_path = concatenate((self.current_path,p))
        return
    def __add__(self,pathtuple):
        assert len(pathtuple)==3
        self.addpath(*pathtuple)
        return self
    def plot(self):
        ax.plot(*[self.current_path[:,j] for j in range(3)],
            color='k')
        return
    def small_pieces(self,piece_length=0.01e-3):
        r"""this is important for getting biot-savart
        right

        Parameters
        ==========
        piece_length: float
            I actually ended up deciding on this by
            making sure that my curves look smooth
        """
        dl = diff(self.current_path,axis=0)
        dl_size = sqrt((dl**2).sum(axis=1))
        dl_size = r_[0,dl_size]
        progress_along_length = cumsum(dl_size)
        print "length of wire is",progress_along_length[-1]
        print "was input in",len(progress_along_length),"pieces"
        # interpolation must be linear to keep straight
        # pieces straight!
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
        print "dividing into",len(new_progress),"pieces"
        self.current_path = stack((
            x_coords(new_progress),
            y_coords(new_progress),
            z_coords(new_progress))).T
        self.is_smooth = True
        return self
    def calculate_biot(self,grid,
            threshold=1e-3):
        r"""calculate biot-savart on grid

        Parameters
        ==========
        grid: ndarray
            (# points) x 3
            where 3 is x,y,z
        threshold: float
            field not calculated within threshold of
            the wire (to avoid the very large vectors)
            -- this is done by setting to nan

        Returns
        =======
            (# points) x 3
            where 3 is x,y,z *of the field vector*
            at the position given by `grid`
        """
        assert hasattr(self,'is_smooth') and self.is_smooth, "you must smooth before running biot-savart"
        # this I realize is important
        dl = diff(self.current_path,axis=0)
        centerpoint = (self.current_path[:-1,:]
                +self.current_path[1:,:])/2
        # the following would probably be more clear in
        # pyspecdata, but we don't have the cross
        # product implemented
        #
        # we need dimensions:
        # (grid points) x (current path points) x 3
        # where current path points is the integration
        # variable
        dl = dl[newaxis,:,:]
        grid = grid[:,newaxis,:]
        centerpoint = centerpoint[newaxis,:,:]
        rprime = grid-centerpoint
        rprime_len = sqrt((rprime**2
                ).sum(axis=-1,keepdims=True))
        rprime_len[rprime_len < threshold] = nan
        retval = mu_0/4/pi*(
                cross(dl,rprime)/rprime_len**3).sum(axis=1)
        return retval

# starting with bottom piece, from halfway-point

p1 = path_obj(Z0,
        r_[-length/2, length/2],
        y_c/2)
p1 += (Z0,
        length/2,
        r_[y_c/2, width+y_c/2])
p1 += (Z0,
        r_[length/2, -length/2],
        width+y_c/2)
p1 += (Z0,
        -length/2,
        r_[width+y_c/2,y_c/2])

p2 = path_obj(Z0,
        r_[-length/2, length/2],
        -1*y_c/2)
p2 += (Z0,
        length/2,
        -1*r_[y_c/2, width+y_c/2])
p2 += (Z0,
        r_[length/2, -length/2],
        -1*(width+y_c/2))
p2 += (Z0,
        -length/2,
        -1*r_[width+y_c/2,y_c/2])

p3 = path_obj(-1*Z0,
        r_[-length/2, length/2],
        y_c/2)
p3 += (-1*Z0,
        length/2,
        r_[y_c/2, width+y_c/2])
p3 += (-1*Z0,
        r_[length/2, -length/2],
        width+y_c/2)
p3 += (-1*Z0,
        -length/2,
        r_[width+y_c/2,y_c/2])

p4 = path_obj(-1*Z0,
        r_[-length/2, length/2],
        -1*y_c/2)
p4 += (-1*Z0,
        length/2,
        -1*r_[y_c/2, width+y_c/2])
p4 += (-1*Z0,
        r_[length/2, -length/2],
        -1*(width+y_c/2))
p4 += (-1*Z0,
        -length/2,
        -1*r_[width+y_c/2,y_c/2])
p1.small_pieces()
p2.small_pieces()
p3.small_pieces()
p4.small_pieces()

p1.plot()
p2.plot()
p3.plot()
p4.plot()
# {{{ again, this would be more legible/compact w/ pyspec:
# x = nddata(r_[-R:R:10j],'x')
# ...
# grid = concat([x*y.ones()*z.ones(),
#        x.ones()*y*z.ones(),
#        x.ones()*y.ones()*z],'gridpoints').reorder('gridpoints',first=False).smoosh(['x','y','z'])
# but this time, we are missing the equivalent of
# ones_like (the .ones() above)
# 
# first, I define a grid of ones that covers the x,y,
# and z points I want
x_points = r_[0]
#y_points = r_[-0.5*y_dist1:0.5*y_dist1:11j]
y_points = r_[-Z0,0,Z0]
z_points = r_[-1*(y_c+width):y_c+width:106j]
ones_grid = ones((len(x_points),
    len(y_points),
    len(z_points)))
# now give the coordinates of the grid
x_points = x_points[:,newaxis,newaxis]
y_points = y_points[newaxis,:,newaxis]
z_points = z_points[newaxis,newaxis,:]
# now stack the coordinates
point_grid = stack((x_points*ones_grid,
    y_points*ones_grid,
    z_points*ones_grid)).transpose(
            (1,2,3,0) # put the outer (stack) dimension on the inside
            ).reshape((-1,3))
# }}}
fields = p1.calculate_biot(point_grid) + p2.calculate_biot(point_grid) + p3.calculate_biot(point_grid) + p4.calculate_biot(point_grid)
print shape(fields.reshape(x_points.size,y_points.size,z_points.size,3))
fields_asgrid = fields.reshape(x_points.size,y_points.size,z_points.size,3) # a 3D grid -- with vector components for each as the last (inner) dim

ax.quiver(*(
    [point_grid[:,j] for j in xrange(3)]
    +[500*fields[:,j] for j in xrange(3)]
    ))
# {{{ all of this is to get equal sized axes
max_width = max(diff(stack((
        array(ax.get_xlim()),
        array(ax.get_ylim()),
        array(ax.get_zlim()))),axis=1))
midpoint = mean(stack((
    array(ax.get_xlim()),
    array(ax.get_ylim()),
    array(ax.get_zlim()))),axis=1)
newlims = stack((midpoint-max_width/2,
    midpoint+max_width/2))
ax.set_xlim(newlims[:,0])
ax.set_ylim(newlims[:,1])
ax.set_zlim(newlims[:,2])
#ax.set_xlim(-0.01,0.01)
#ax.set_ylim(-0.01,0.01)
#ax.set_zlim(-0.01,0.01)
print newlims
# }}}
figure(2)
# {{{ to reduce to a 2d grid, index 0 along the x dimension, which is only 1
#     point thick -- for the vector component, select the x component
y_2d = y_points[0,:,:]
z_2d = z_points[0,:,:]
contourf(y_2d*ones_like(z_2d),z_2d*ones_like(y_2d),fields_asgrid[0,:,:,0],
        100)
colorbar()
# }}}
figure(3)
# {{{ now, to reduce to 1d, just select the central index along y
y_idx = int(0.5*fields_asgrid.shape[1]+0.5) # use the int(x + 0.5) trick to round + int convert
plot(z_points[0,0,:]/1e-3,fields_asgrid[0,y_idx,:,0]/1e-6,'k')
ylabel(r'field / $\mu$T')
xlabel('position / mm')
axvspan(-10,10,alpha=0.3,color='b')
#savefig('20190722_gradients_planar.pdf',
#        transparent=True,
#        bbox_inches='tight',
#        pad_inches=0)
# }}}
show()
