# Trial object is all information in one trial. Each subject should have 8 trials (4 days * 2 per day)
import os
import numpy as np
import mne
from detect_peaks import detect_peaks

def parseImpedance(filename):
    filedata = np.genfromtxt(filename, skip_header=23, comments='$', skip_footer=2) # default comment is # mark, which is used in the file
    filedata_lastTwoRow = np.genfromtxt(filename, skip_header=87, comments='$')
    impedance = np.concatenate((filedata[:,6], filedata_lastTwoRow[:,4]),axis=0)
    return impedance

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
    impedanceBefore = -1
    impedanceAfter = -1
    # locationFile = -1 # 60Ch_EOGlayout.locs
    impedanceRemove = -1
    info = -1
    gaitSegments_rmOutliers = -1 # gait cycles. each row contains the starting and ending time of one cycle

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

        
    def readEEG(self):
        self.eegFile = np.loadtxt(self.filePath + self.date + '_eeg_' + self.fileID + '.txt', skiprows=1)
         

    def readImpedance(self):
        try:
            self.triID % 2 == 1
        except EnvironmentError:
            print 'This trial does not contain impedance records'

        # Remove this six channels from impedance recording
        # 17,22,41,46 are EOG, 65 and 66 are GND and REF
        # when used in numpy, they need to shift by 1!!!!
        self.impedanceRemove = np.array([17, 22, 41, 46, 65, 66])

        allFiles = os.listdir(self.filePath)
        for f in allFiles:
            if f[-9:-4]=='after':
                # read file and remove 6 non-EEG channels
                tempImpedance = np.delete(parseImpedance(self.filePath+f), self.impedanceRemove-1)
                # replace NaN by a big value (60, which is vmax)
                tempImpedance[np.isnan(tempImpedance)] = 60
                self.impedanceAfter = tempImpedance
            if f[-10:-4]=='before':
                # read file and remove 6 non-EEG channels
                tempImpedance = np.delete(parseImpedance(self.filePath + f), self.impedanceRemove - 1)
                # replace NaN by a super big value (100)
                tempImpedance[np.isnan(tempImpedance)] = 60
                self.impedanceBefore = tempImpedance


    def readChannelLocation(self):
        # this info object only contains 60 channels, which are all EEG data
        readMontage = mne.channels.read_montage(kind='60Ch_EOGlayout', path='resources/')
        self.info = mne.create_info(readMontage.ch_names, 100, ch_types='eeg', montage=readMontage)


    def gaitSegmentation(self, check = False):
        # find peaks and identify adnormal intervals
        peaks = detect_peaks(self.decoderFile[:,2], mph=30, mpd=100, valley=True, show=check)
        peakDiff = np.diff(peaks)
        peakMean = np.mean(peakDiff[20:-15])
        peakStd = np.std(peakDiff[20:-15])
        peakOutlierIdx = np.where( (peakDiff>peakMean+peakStd*3) | (peakDiff<peakMean-peakStd*3) )
        # turn peaks into segments, and remove outlier segments
        gaitSegments = np.zeros((len(peaks)-1,2))
        for i in range(0,len(gaitSegments)):
            gaitSegments[i,0] = peaks[i]
            gaitSegments[i,1] = peaks[i+1]
        mask = np.ones(len(peaks)-1, dtype=bool)
        mask[peakOutlierIdx] = False
        self.gaitSegments_rmOutliers = gaitSegments[mask,...]
        # console print
        if check==True:
            if len(peakOutlierIdx)==0:
                print '--- No outlier peaks ---'
            else:
                print 'Outlier peaks (outside 3 std range) are:', peakOutlierIdx[0]
                print 'peakDiffMean = ' + str(peakMean)
                print 'peakDiffStd = ' + str(peakStd)


