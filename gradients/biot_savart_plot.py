from pyspecdata import *

planar = np.load('planar_gradient.npz')
curved = np.load('curved_gradient.npz')

figure()
plot(curved['field'],
        curved['points'],
        c='red',
        alpha=0.75,
        label='curved')
plot(planar['field'],
        planar['points']
        ,c='navy',
        alpha=0.75,
        label='planar')
xlabel(r'$B_{z}$ \ $\frac{mT}{turn}$')
ylabel(r'$z$ \ cm')
axhline(0.5,linestyle=':',c='black')
axhline(-0.5,linestyle=':',c='black')
legend()
savefig('20190719_distance_gradients.pdf',
       transparent=True,
       bbox_inches='tight',
       pad_inches=0)
show()
