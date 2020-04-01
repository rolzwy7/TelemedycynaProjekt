# import numpy as np
# import matplotlib.pyplot as plt


# import argparse
# parser = argparse.ArgumentParser()
# parser.add_argument("test")
# args = parser.parse_args()


# fig = plt.figure()
# ax = plt.axes(projection='3d')
# ax = plt.axes(projection='3d')

# # Data for a three-dimensional line
# zline = np.linspace(0, 15, 1000)
# xline = np.sin(zline)
# yline = np.cos(zline)
# ax.plot3D(xline, yline, zline, 'gray')

# # Data for three-dimensional scattered points
# zdata = 15 * np.random.random(100)
# xdata = np.sin(zdata) + 0.1 * np.random.randn(100)
# ydata = np.cos(zdata) + 0.1 * np.random.randn(100)
# ax.scatter3D(xdata, ydata, zdata, c=zdata, cmap='Greens');

# plt.show()


# from mpl_toolkits.mplot3d import Axes3D
# import matplotlib.pyplot as plt
# import numpy as np


# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')

# # Make data
# u = np.linspace(0, 2 * np.pi, 100)
# v = np.linspace(0, np.pi, 100)
# x = 10 * np.outer(np.cos(u), np.sin(v))
# y = 10 * np.outer(np.sin(u), np.sin(v))
# z = 10 * np.outer(np.ones(np.size(u)), np.cos(v))

# # Plot the surface
# ax.plot_surface(x, y, z, color='b')

# plt.show()



import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

def drawSphere(xCenter, yCenter, zCenter, r):
    #draw sphere
    u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
    x=np.cos(u)*np.sin(v)
    y=np.sin(u)*np.sin(v)
    z=np.cos(v)
    # shift and scale sphere
    x = r*x + xCenter
    y = r*y + yCenter
    z = r*z + zCenter
    return (x,y,z)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

xi, yi, zi, ri = 5, 5, 5, 10
(xs,ys,zs) = drawSphere(xi,yi,zi,ri)
ax.plot_wireframe(xs, ys, zs, color="r")

plt.show()