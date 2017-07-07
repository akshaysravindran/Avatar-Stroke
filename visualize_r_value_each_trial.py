import matplotlib.pyplot as plt
import statsmodels.api as sm  # for some reason also need to install patsy

from asp.load import Trial
from asp.rolling_r_value import rolling_r_value  # a small function to compute rolling r value

# ------ parameters ------
winLen = 1000
r_fs = 500
timeEEGbegin = 570 # beginning of EEG control

for trialId in range(1,2):
    t = Trial(1, trialId)
    t.readDecoder()

    r = rolling_r_value(t.decoderFile[:,1], t.decoderFile[:,7], winLen, r_fs)
    # -- the old way to create time series in x-axis is purely
    # through the sampling rate and protocol. However, the sampling
    # rate is about 86Hz rather than 100. So it's better to use the
    # recorded time in the x-axis
    # r_windowTime = np.array(range(0, r.size*5, 5))
    r_time = t.decoderFile[0:-winLen:r_fs, 0].copy() #pick a sample every r_fs samples


    # figure
    plt.figure()
    plt.plot(r_time/60.0, r,'.')
    plt.xlabel('Time (min)')
    plt.ylabel('Correlation coefficient')
    # a vertical line to mark the beginning of EEG control
    ax = plt.gca()
    plt.plot([timeEEGbegin/60, timeEEGbegin/60], ax.get_ylim(), 'k-', lw=2)
    plt.autoscale(enable=True, axis='y', tight=True)
    # curve fitting
    fittedCurve = sm.nonparametric.lowess(r, r_time/60.0, frac=0.5)
    # the line above accepts Y coordinate before X.
    plt.plot(fittedCurve[:,0], fittedCurve[:,1])

plt.show()







print 'whatsup'
