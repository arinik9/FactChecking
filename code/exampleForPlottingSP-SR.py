#!/usr/bin/python

#source: http://stackoverflow.com/questions/18897885/qualitative-heatmap-plot-python
import numpy as np
import matplotlib.pyplot as plt

data = np.random.random((20, 3))
print(data)
plt.imshow(data, interpolation='none', aspect=3./20)

plt.xticks(range(3), ['a', 'b', 'c'])
# plt.yticks(range(3), ['aa', 'bb', 'cc'])
plt.jet()
plt.colorbar()

plt.show()
