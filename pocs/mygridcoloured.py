import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors

N = 5   # nb of rows
M = 7   # nb of columns
# make an empty data set
data = np.ones((N, N)) * np.nan
data[0, 0:7] = 5
data[1, 0:7] = 4
data[2, 0:7] = 3
data[3, 0:7] = 2
data[4, 0:7] = 1

# make a figure + axes
fig, ax = plt.subplots(1, 1, tight_layout=True)
# make color map
my_cmap = matplotlib.colors.ListedColormap(['#ff0000', '#ff0180', '#ff6701', '#ffff00', '#00ff00'])
# set the 'bad' values (nan) to be white and transparent
my_cmap.set_bad(color='w', alpha=0)
# draw the grid
for x in range(N + 1):
    ax.axhline(x, lw=2, color='k', zorder=5, alpha=0.2)
    ax.axvline(x, lw=2, color='k', zorder=5, alpha=0.2)
# draw the boxes
ax.imshow(data, interpolation='none', cmap=my_cmap, extent=[0, N, 0, N], zorder=0)
# turn off the axis labels
ax.axis('off')
plt.show()
