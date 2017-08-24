import matplotlib.pyplot as plt
from scipy import interpolate
import numpy as np


def spectrogram_timewrap(vector, new_bins, NFFT=32, Fs=100, noverlap=24):
    # 2017-7-2 compute spectrogram of the input vector (an EEG channel or source), and time wrap it
    # to new time points, given in the time vector new_bins
    # for example, new_bins = np.arange(0, 20, 0.5) 
    # plot controls whether to generate figure or not 

    # spectrogram
    Pxx, freqs, bins, im = plt.specgram(vector, NFFT=NFFT, Fs=Fs, noverlap=noverlap,
                                        pad_to=None, window=plt.mlab.window_hanning)
    # time wrap
    Pxx_new = np.zeros([Pxx.shape[0], len(new_bins)])
    for i in range(0, Pxx.shape[0]):
        tck = interpolate.splrep(bins, Pxx[i,:], s=0)
        Pxx_new[i,] = interpolate.splev(np.array(new_bins), tck, der=0)

        # PSD has to be positive. Otherwise can't apply db scale
        Pxx_new_positive = Pxx_new.copy()
        temp = np.ravel(Pxx_new_positive)
        for k in range(0, len(temp)): #prev needs a positive value to start with
            if temp[k]>0:
                prev = temp[k]
                break
        for i in range(0, Pxx_new_positive.shape[0]): # make every element positive
            for j in range(0, Pxx_new_positive.shape[1]):
                if Pxx_new_positive[i, j] < 0:
                    Pxx_new_positive[i, j] = prev
                prev = Pxx_new_positive[i, j]
                Pxx_new_positive[i, j] = 10 * np.log10(Pxx_new_positive[i, j]) # db power

    return (Pxx_new_positive, freqs)


def plotSpectrogram(Pxx, freqs, bins, plotColorbar=False, rangeLimit=False):
    # remove outliers in Pxx in order to keep colorbar meanfuling
    if rangeLimit==True:
        for i in range(0, len(Pxx)):
            if Pxx[i]>10:
                Pxx[i] = 10
            if Pxx[i]<-10:
                Pxx[i] = -10

    fig = plt.figure()
    ax = fig.add_subplot(111)

    imshow_matrix = np.flipud(t.gaitSpecgramMean)
    im = ax.imshow(imshow_matrix, extent=[0, 100, 0, t.gaitSpecgramMeanFreqs[-1]], aspect='auto', interpolation='gaussian', cmap='rainbow')

    ax.set_xlabel('Averaged Gait (%)')
    ax.set_ylabel('Frequency (Hz)')

    if plotColorbar == True:
        cb = fig.colorbar(im)
        cb.set_label('dB')
