import matplotlib.pyplot as plt
import statsmodels.api as sm  # for some reason also need to install patsy

from headers.classTrial import Trial
from headers.windowed_R import windowed_R  # a small function to compute rolling r value

# ------ parameters ------
winLen = 1000
r_fs = 500
timeEEGbegin = 570 # beginning of EEG control

plt.figure()
plt.xlabel('Time (min)')
plt.ylabel('Correlation coefficient')

for trialId in range(1,9):
    t = Trial(1, trialId)
    t.readDecoder()

    r = windowed_R(t.decoderFile[:,1], t.decoderFile[:,7], winLen, r_fs)
    # -- the old way to create time series in x-axis is purely
    # through the sampling rate and protocol. However, the sampling
    # rate is about 86Hz rather than 100. So it's better to use the
    # recorded time in the x-axis
    # r_windowTime = np.array(range(0, r.size*5, 5))
    r_time = t.decoderFile[0:-winLen:r_fs, 0].copy() #pick a sample every r_fs samples

    # plt.plot(r_time/60.0, r,'.')

    # curve fitting
    fittedCurve = sm.nonparametric.lowess(r, r_time/60.0, frac=0.3)
    # the line above accepts Y coordinate before X.
    plt.plot(fittedCurve[:,0], fittedCurve[:,1], label='Trial '+str(trialId))

# a vertical line to mark the beginning of EEG control
ax = plt.gca()
plt.plot([timeEEGbegin/60, timeEEGbegin/60], ax.get_ylim(), 'k-', lw=2)
plt.autoscale(enable=True, axis='y', tight=True)

plt.legend()

plt.show()
