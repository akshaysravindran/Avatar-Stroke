import numpy as np

def parseImpedance(filename):
    filedata = np.genfromtxt(filename, skip_header=23, comments='$', skip_footer=2) # default comment is # mark, which is used in the file
    filedata_lastTwoRow = np.genfromtxt(filename, skip_header=87, comments='$')
    impedance = np.concatenate((filedata[:,6], filedata_lastTwoRow[:,4]),axis=0)
    return impedance
