from pyspecdata import *
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import interp1d
clf()
ax = subplot(111, projection='3d')

width = 3.0e-2 # width of one rectangular array
length = 6.0e-2 # length of one rectangular array
y_dist1 = 2.5e-2

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
    if isscalar(x):
        x = x*ones_like(z)
        y = y*ones_like(z)
    elif isscalar(z):
        z = z*ones_like(x)
        y = y*ones_like(x)
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
p1 = path_obj(r_[-length/2,length/2],y_dist1,0.25e-2)
p1 += (length/2,y_dist1,r_[0.25e-2,3.25e-2])
p1 += (r_[length/2,-length/2],y_dist1,3.25e-2)
p1 += (-length/2,y_dist1,r_[3.25e-2,0.25e-2])
p1 += (r_[-length/2,length/2],y_dist1,-1*0.25e-2)
p1 += (length/2,y_dist1,-1*r_[0.25e-2,3.25e-2])
p1 += (r_[length/2,-length/2],y_dist1,-1*3.25e-2)
p1 += (-length/2,y_dist1,-1*r_[3.25e-2,0.25e-2])
p1.small_pieces()

p2 = path_obj(r_[-length/2,length/2],-1*y_dist1,0.25e-2)
p2 += (length/2,-1*y_dist1,r_[0.25e-2,3.25e-2])
p2 += (r_[length/2,-length/2],-1*y_dist1,3.25e-2)
p2 += (-length/2,-1*y_dist1,r_[3.25e-2,0.25e-2])
p2 += (r_[-length/2,length/2],-1*y_dist1,-1*0.25e-2)
p2 += (length/2,-1*y_dist1,-1*r_[0.25e-2,3.25e-2])
p2 += (r_[length/2,-length/2],-1*y_dist1,-1*3.25e-2)
p2 += (-length/2,-1*y_dist1,-1*r_[3.25e-2,0.25e-2])
p2.small_pieces()
p1.plot()
p2.plot()
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
x_points = r_[0] #r_[-0.5*y_dist1:0.5*y_dist1:11j]
y_points = r_[0]
z_points = r_[-width:width:106j]
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
fields1 = p1.calculate_biot(point_grid) + p2.calculate_biot(point_grid)


print x_points
print z_points
y_fields = (fields1[:,1].reshape(106,-1))
print shape(y_fields)
print shape(z_points)
plot_distance = False
if plot_distance:
    figure()
    plot(y_fields[:,1],z_points.squeeze()*1e2)
    xlabel(r'$B_{0,z}$ \ $\frac{T}{turn}$')
    ylabel(r'$z$ \ cm')
    savefig('20190719_distance_gradients_planar.pdf',
            transparent=True,
            bbox_inches='tight',
            pad_inches=0)
    show()
    quit()

ax.quiver(*(
    [point_grid[:,j] for j in xrange(3)]
    +[500*fields1[:,j] for j in xrange(3)]
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
# }}}
show()
