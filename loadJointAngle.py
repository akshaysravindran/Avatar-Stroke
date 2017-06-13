import numpy as np
import matplotlib.pyplot as plt

data = np.loadtxt('../Avatar Stroke Data/2017_6_5_decoder_0002.txt', skiprows=1)

plt.figure()
plt.plot(data[:, 0], data[:, 1])
plt.plot(data[:, 0], data[:, 7])
plt.show()


print('whats up')
