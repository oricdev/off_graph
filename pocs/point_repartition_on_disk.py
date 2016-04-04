from __future__ import division
from numpy import pi
import numpy
import matplotlib.pyplot as plt

# The algorithm below is strongly inspired from the one available here:
# http://stackoverflow.com/questions/5408276/sampling-uniformly-distributed-random-points-inside-a-spherical-volume
# This is here a repartition on a disk instead on a sphere (1 angle required and 2 coordinates)


class PointRepartition:
    def __init__(self, nb_particles):
        self.number_of_particles = nb_particles

    def new_positions_spherical_coordinates(self):
        radius = numpy.random.uniform(0.0, 1.0, (self.number_of_particles, 1))
        theta = numpy.random.uniform(-1., 1., (self.number_of_particles, 1)) * pi
        x = radius * numpy.sin(theta)
        y = radius * numpy.cos(theta)
        return (x, y)

# X points (almost) uniformly spotted on a disk
sample = PointRepartition(25)
x, y = sample.new_positions_spherical_coordinates()
print "x = %r // y = %r" % (x, y)
v_x = []
v_y = []
for x0, y0 in zip(x, y):
    print "%r // %r " % (x0[0], y0[0])
    v_x.append(x0[0]*100)
    v_y.append(y0[0]*100)
plt.scatter(v_x, v_y)
plt.show()