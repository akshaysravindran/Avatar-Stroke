# Trial object is all information in one trial. Each subject should have 8 trials (4 days * 2 per day)
import os
import numpy as np

class Trial:
    filePath = ''  # file path of the folder
    subID = -1
    triID = -1
    date = -1  # eg. 2017_6_7
    fileID = -1  # four digit sequence like 0001
    subIDStr = ''
    triIDStr = ''
    eegFile = -1  # raw eeg file
    decoderFile = -1  # raw decoder file
    conductorFile = -1  # raw conductor file

    def __init__(self, subID, triID):
        # sanity check
        try:
            0 < subID < 100
        except ValueError:
            print 'subID wrong value.'
        try:
            0 < triID < 9
        except ValueError:
            print 'triID wrong value.'

        # figuring out the path and file names
        self.subID = subID
        self.triID = triID
        # if SubId<10, add '0' in front to make double digit
        if subID < 10:
            self.subIDStr = '0' + str(subID)
        else:
            self.subIDStr = str(subID)
        # same for TriId
        if triID < 10:
            self.triIDStr = '0' + str(triID)
        else:
            self.triIDStr = str(triID)
        # file path
        self.filePath = '../Avatar Stroke Data/SS' + self.subIDStr + '-T' + self.triIDStr + '/'
        try:
            os.path.isdir(self.filePath)
        except EnvironmentError:
            print 'No data directory'

        # identify the date and fileID string so it's easier to read files
        allFiles = os.listdir(self.filePath)
        for f in allFiles:
            if f[0:3] == '201':
                dashCount = 0
                for i in range(0, len(f)):
                    if f[i] == '_':
                        dashCount += 1
                        if dashCount == 3:
                            self.date = f[0:i]
                            break
                self.fileID = f[-8:-4]
                break

    def readDecoder(self):
        self.decoderFile = np.loadtxt(self.filePath + self.date + '_decoder_' + self.fileID + '.txt', skiprows=1)

