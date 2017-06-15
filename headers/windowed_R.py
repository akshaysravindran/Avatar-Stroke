import numpy as np

# rolling r value between two signals.
# v1 and v2 are both numpy vectors
# winLen is a positive integer
# r_fs is the window moving interval. If r_fs=1, the windows moves by every sample.
def windowed_R(v1, v2, winLen, r_fs):
    try:
        (v1.shape == [0, 1] or [1, 0]) and (v2.shape == [0, 1] or [1, 0])
    except ValueError:
        print 'windowed_R wrong input vector'

    len = v1.size
    r = np.zeros((len - winLen)/r_fs+1)
    tempWinL=0 # high and low bound of the current window
    tempWinH=0
    for i in range(0, r.size):
        tempWinL = i*r_fs
        tempWinH = i*r_fs+winLen
        # note that corrcoef() always return 1 on its diagnal
        r[i] = np.corrcoef(v1[tempWinL:tempWinH], v2[tempWinL:tempWinH], rowvar=True)[0, 1]
        # print v1[i:i + winLen]
        # print v2[i:i + winLen]
        # print np.corrcoef(v1[i:i + winLen], v2[i:i + winLen], rowvar=True)
    return r