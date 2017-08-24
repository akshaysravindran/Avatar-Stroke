import numpy as np

def cutArray(arr, t_start, t_end):
# Summary: The first column of the input array is time, other columns are data. Cut part of this array based on start/end time
# prerequisite:
# Input: n-column array like rCurveHip, and the starting and ending time of segmentation
# Output: a segment of this array
# Date: 2017-7-28

    t_start_idx = np.argmax (arr[:,0]>t_start)
    t_end_idx = np.argmax (arr[:,0]>t_end)

    output = arr[t_start_idx:t_end_idx, :]

    return output