from headers.classTrial import Trial
import mne
import numpy as np
import matplotlib.pyplot as plt

trialList = [Trial(1,i) for i in range(1,9)]

for triID in range(8):
    trialList[triID].readImpedance()
    trialList[triID].readChannelLocation()

fig, axarr = plt.subplots(2,4)

for i in range(0,4):
    triID = i*2
    if type(trialList[triID].impedanceBefore) != int:
        mne.viz.plot_topomap(trialList[triID].impedanceBefore, trialList[triID].info,
                         contours=0, cmap='hot_r', vmin=0, vmax=60, axes=axarr[0, i])
    else:
        axarr[0, i].axis('off')
    if type(trialList[triID].impedanceAfter) != int:
        mne.viz.plot_topomap(trialList[triID].impedanceAfter, trialList[triID].info,
                         contours=0, cmap='hot_r', vmin=0, vmax=60, axes=axarr[1, i])
    else:
        axarr[1, i].axis('off')