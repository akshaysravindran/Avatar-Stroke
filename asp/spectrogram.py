import matplotlib.pyplot as plt
from scipy import interpolate
import numpy as np


def spectrogram_timewrap(vector, new_bins, plot, NFFT=128, Fs=100, noverlap=80):
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
        tck = interpolate.splrep(bins, Pxx[i,], s=0)
        Pxx_new[i,] = interpolate.splev(np.array(new_bins), tck, der=0)

        # PSD has to be positive. Otherwise can't apply db scale
        Pxx_new_positive = Pxx_new.copy()
        prev = Pxx_new_positive[0, 0]
        for i in range(0, Pxx_new_positive.shape[0]):
            for j in range(0, Pxx_new_positive.shape[1]):
                if Pxx_new_positive[i, j] < 0:
                    Pxx_new_positive[i, j] = prev
                prev = Pxx_new_positive[i, j]

        if plot:
            plotSpectrogram(Pxx_new_positive)

    return (Pxx_new_positive, freqs, new_bins)

	
def plotSpectrogram(result):
    # timeLength = rsult.shape[1]/100

    fig = plt.figure()
    ax = fig.add_subplot(111)

    imshow_matrix = np.flipud(10 * np.log10(result))
    im = ax.imshow(imshow_matrix, extent=[0, 20, 0, 50], aspect='auto')
    cb = fig.colorbar(im)
    cb.set_label('dB')

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Frequency (Hz)')

    fig.show()
