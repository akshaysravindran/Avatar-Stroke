# Trial object is all information in one trial. Each subject should have 8 trials (4 days * 2 per day)
import os
import numpy as np
# import mne
import matplotlib.pyplot as plt
from detect_peaks import detect_peaks
from asp.spectrogram import spectrogram_timewrap
from asp.rolling_r_value import rolling_r_value  # a small function to compute rolling r value
from asp.cutArray import cutArray
import statsmodels.api as sm  # for some reason also need to install patsy
from numpy import cos, sin, pi

def parseImpedance(filename):
    filedata = np.genfromtxt(filename, skip_header=23, comments='$', skip_footer=2) # default comment is # mark, which is used in the file
    filedata_lastTwoRow = np.genfromtxt(filename, skip_header=87, comments='$')
    impedance = np.concatenate((filedata[:,6], filedata_lastTwoRow[:,4]),axis=0)
    return impedance

class Trial:
    def __init__(self, subID, triID):
        self.filePath = ''  # file path of the folder
        self.subID = -1
        self.triID = -1
        self.date = -1  # eg. 2017_6_7
        self.fileID = -1  # four digit sequence like 0001
        self.subIDStr = ''
        self.triIDStr = ''
        self.fs = 100
        self.eegFile = -1  # raw eeg file
        self.decoderFile = -1  # raw decoder file
        self.conductorFile = -1  # raw conductor file
        self.impedanceBefore = -1
        self.impedanceAfter = -1
        # self.locationFile = -1 # 60Ch_EOGlayout.locs
        self.impedanceRemove = -1
        self.info = -1
        self.gaitSegments_rmOutliers = -1 # gait cycles. each row contains the starting and ending time of one cycle
        self.gaitSpecgramMean = -1
        self.gaitSpecgramMeanFreqs = -1
        self.rCurveHip = -1 # regressed curve of the windowed r values
        self.rCurveKnee = -1
        self.rCurveAnkle = -1
        self.rRightHipByGait = self.rRightKneeByGait = self.rRightAnkleByGait = self.rLeftHipByGait = self.rLeftKneeByGait = self.rLeftAnkleByGait = -1
        self.rAllJointByGait = -1
        self.rTrain = self.rTest = self.rTrainMean = self.rTestMean = self.rTrainMedian = self.rTestMedian = -1
        self.heel = -1 # trajectory of the heel in sagittal plane.
        self.events = -1 # a dict with four times: treadmill starts, brain control starts, brain control ends, treadmill ends
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
        self.readChannelLocation() # creates info structure
        self.eegFile = np.loadtxt(self.filePath + self.date + '_eeg_' + self.fileID + '.txt', skiprows=1)
        # remove EOG channels to match the info
        # the first column in eegfile is time. the four eog channel's index count from 1. Together, they balance out.
        self.eeg = np.delete(self.eegFile, np.array([17, 22, 41, 46]), 1)

    def readConductor(self):
        self.conductorFile = np.loadtxt(self.filePath + self.date + '_conductor_' + self.fileID + '.txt', skiprows=2)
        tdmStart = self.conductorFile [np.where(self.conductorFile[:,1]==8)[0][0], 0]
        brainStart = self.conductorFile [np.where(self.conductorFile[:,1]==8)[0][1], 0]
        brainEnd= self.conductorFile [np.where(self.conductorFile[:,1]==10)[0][1], 0]
        triEnd= self.conductorFile [np.where(self.conductorFile[:,1]==9)[0][0], 0]
        self.events = {'tdmStart':tdmStart, 'brainStart': brainStart, 'brainEnd': brainEnd, 'triEnd': triEnd}
        # for example, events = 30 450 750 780


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
        import mne # mne requires PyQt5. It may mess up with %matplotlib qt
        readMontage = mne.channels.read_montage(kind='60Ch_EOGlayout', path='resources/')
        self.info = mne.create_info(readMontage.ch_names, self.fs, ch_types='eeg', montage=readMontage)


    def gaitSegmentation(self, check = False):
        # gait only starts after the TdmStart
        start_idx = np.argmax (self.decoderFile[:,0]>self.events['tdmStart'])
        # find peaks and identify adnormal intervals
        peaks = detect_peaks(self.decoderFile[:,2], mph=30, mpd=100, valley=True, show=check)
        peakDiff = np.diff(peaks)
        peakMean = np.mean(peakDiff[20:-15])
        peakStd = np.std(peakDiff[20:-15])
        peakOutlierIdx = np.where( (peakDiff>peakMean+peakStd*3) | (peakDiff<peakMean-peakStd*3) ) # gaits outside 3 std are a bit abnormal. but don't remove
        peakOutlierRemoveIdx = np.where( peakDiff>300 ) # remove gaits that are longer than 3 sec
        peakOutlierStandIdx = np.where( peaks<start_idx) # remove gaits that are before the treadmill starts

        # turn peaks into segments
        gaitSegments = np.zeros((len(peaks)-1,2))
        for i in range(0,len(gaitSegments)):
            gaitSegments[i,0] = peaks[i]
            gaitSegments[i,1] = peaks[i+1]

        # remove outlier segments
        mask = np.ones(len(peaks)-1, dtype=bool)
        mask[peakOutlierRemoveIdx] = False # note which version of outlier to remove
        mask[peakOutlierStandIdx] = False
        self.gaitSegments_rmOutliers = gaitSegments[mask,...]
        # console print
        if check==True:
            # text alert
            if len(peakOutlierIdx)==0:
                print '--- No outlier peaks ---'
            else:
                print 'Outlier peaks (outside 3 std range) are:', peakOutlierIdx[0]
                print 'peakDiffMean = ' + str(peakMean)
                print 'peakDiffStd = ' + str(peakStd)
            # visulization
            for i in range(len(peakOutlierIdx)):
                x_coordinate = peaks[peakOutlierIdx[i]]
                y_coordinate = self.decoderFile[x_coordinate,2]
                plt.plot(x_coordinate, y_coordinate,'go', markersize=5)
                x_remove_coordinate = peaks[peakOutlierRemoveIdx[i]]
                y_remove_coordinate = self.decoderFile[x_remove_coordinate,2]
                plt.plot(x_remove_coordinate, y_remove_coordinate,'mo', markersize=5, alpha=1.0)
                x_remove_coordinate = peaks[peakOutlierStandIdx[i]]
                y_remove_coordinate = self.decoderFile[x_remove_coordinate,2]
                plt.plot(x_remove_coordinate, y_remove_coordinate,'ko', markersize=5, alpha=1.0)

    def gaitSpecgrams(self, channel, mode, ):
    # each gait is an epoch, which has a spectrogram
    # these spectrograms are time-warpped into same length (100)
    # mode can be EEG or ICA
    # channel indicates which channel to plot. EEG channel k is indexed as k-1 in python, which is actually channel k in eegFile

        NFFT = 32

        # initialize epoch_specgrams
        temp = spectrogram_timewrap(self.eegFile[1000:1160,2], np.linspace(0,10,100)) # generate some random plot for its size
        tempSpecgram = temp[0]
        epoch_specgrams = np.zeros([tempSpecgram.shape[0], tempSpecgram.shape[1], self.gaitSegments_rmOutliers.shape[0]])

        # compute specgram in each epoch
        plt.ioff()
        #for i in range(0, self.gaitSegments_rmOutliers.shape[0]):
        for i in range(0, 10):
            if mode=='EEG':
                vec = self.eegFile[int(self.gaitSegments_rmOutliers[i,0]):int(self.gaitSegments_rmOutliers[i,1]),channel]
            #if mode=='ICA':
                # do something. load self.ICAfile
            new_bins = np.linspace(0, (len(vec)-NFFT/2)/float(self.fs), 100)
            result = spectrogram_timewrap(vec, new_bins, NFFT=NFFT, Fs=self.fs, noverlap=24)
            epoch_specgrams[:,:,i] = result[0] - np.repeat(np.mean(result[0],1, keepdims=True), 100, axis=1) # remove the mean
            print 'Working on gaitSpecgram() iteration '+ str(i)
        plt.show()
        plt.ion()
        # specgram averaged over all gait cycles
        self.gaitSpecgramMean = np.mean(epoch_specgrams, 2)
        self.gaitSpecgramMeanFreqs = result[1]

    def RValueByGait(self, side, joint):
    # Summary: compute a r-value within each gait cycle
    # Prerequisit: t.events, gaitSegmentation()
    # Input: joint is a string of either 'hip', 'knee', or 'ankle'
    # Output:
    # Date: 2017/12/12
        try:
            (joint=='hip' or joint=='knee' or joint=='ankle') and (side=='left' or side=='right')
        except ValueError:
            print 'Wrong input options in RvalueByGait()'

        if side=='right':
            if joint=='hip':
                decoderChan = 1
            elif joint=='knee':
                decoderChan = 2
            elif joint=='ankle':
                decoderChan = 3
        elif side=='left':
            if joint=='hip':
                decoderChan = 4
            elif joint=='knee':
                decoderChan = 5
            elif joint=='ankle':
                decoderChan = 6

        result = np.zeros((self.gaitSegments_rmOutliers.shape[0], 2)) # two column: time in minute and r-value
        for gaitId in range(self.gaitSegments_rmOutliers.shape[0]):
            measured =  self.decoderFile[int(self.gaitSegments_rmOutliers[gaitId,0]):int(self.gaitSegments_rmOutliers[gaitId,1]), decoderChan]
            predicted = self.decoderFile[int(self.gaitSegments_rmOutliers[gaitId,0]):int(self.gaitSegments_rmOutliers[gaitId,1]), decoderChan+6]
            result[gaitId, 1] = np.corrcoef(measured, predicted)[0, 1]
            result[gaitId, 0] = self.decoderFile[int((self.gaitSegments_rmOutliers[gaitId, 0]+self.gaitSegments_rmOutliers[gaitId, 1])/2), 0]

        if side=='right':
            if joint=='hip':
                self.rRightHipByGait = result
            elif joint=='knee':
                self.rRightKneeByGait = result
            elif joint=='ankle':
                self.rRightAnkleByGait = result
        elif side=='left':
            if joint=='hip':
                self.rLeftHipByGait = result
            elif joint=='knee':
                self.rLeftKneeByGait = result
            elif joint=='ankle':
                self.rLeftAnkleByGait = result

    def RValueByGaitAllJoint(self):
    # Summary: create a 7-col matrix. First column is time in min, the rest are the r value in six joints.
    # This is just a shortcut of running six individual RValueByGait()
        self.RValueByGait('right','hip')
        self.RValueByGait('right','knee')
        self.RValueByGait('right','ankle')
        self.RValueByGait('left','hip')
        self.RValueByGait('left','knee')
        self.RValueByGait('left','ankle')
        self.rAllJointByGait = np.concatenate((self.rRightHipByGait, self.rRightKneeByGait[:,1].reshape((-1,1)), self.rRightAnkleByGait[:,1].reshape((-1,1)), self.rLeftHipByGait[:,1].reshape((-1,1)), self.rLeftKneeByGait[:,1].reshape((-1,1)), self.rLeftAnkleByGait[:,1].reshape((-1,1))), axis=1)

    # def fitRcurve(self, joint):
    # Summary: fit a curve of the windowed r values in a trial
    # Prerequisit: t.events
    # Input: joint is a string of either 'hip', 'knee', or 'ankle'
    # Output: The returned array (such as rCurveHip) is two-dimensional array. The first column contains time in minutes, and the second column the associated estimated y values.
    # Date:
        # try:
            # joint=='hip' or joint=='knee' or joint=='ankle'
        # except ValueError:
            # print 'Wrong joint to fit r curve.'

        # if joint=='hip':
            # jointId = 0
        # elif joint=='knee':
            # jointId = 1
        # elif joint=='ankle':
            # jointId = 2

        # winLen = 1000
        # r_fs = 500
        # r = rolling_r_value(self.decoderFile[:,1+jointId], self.decoderFile[:,7+jointId], winLen, r_fs)
        # r_time = self.decoderFile[0:-winLen:r_fs, 0].copy() - self.events['brainStart']
        # #pick a sample every r_fs samples

        # # curve fitting
        # if joint=='hip':
            # self.rCurveHip = sm.nonparametric.lowess(r, r_time/60.0, frac=0.3)
        # if joint=='knee':
            # self.rCurveKnee = sm.nonparametric.lowess(r, r_time/60.0, frac=0.3)
        # if joint=='ankle':
            # self.rCurveAnkle = sm.nonparametric.lowess(r, r_time/60.0, frac=0.3)

        ######### need to remove the last two minutes of standing!!!!! #####################

    def heelTrajectory(self):
        bodySize = [332,391,50,-50]
        self.heel = np.zeros((self.decoderFile.shape[0], 2))

        l1 = bodySize[0]    #mm Length of thigh from hip joint to knee joint.
        l2 = bodySize[1]    #mm Length of shank from knee joint to ankle joint.
        xp4 = bodySize[2]   #mm Length of foot from ankle joint to ground (vertical component when standing
        yp4 = bodySize[3]   #mm Distance from ankle joint to heel in the horizontal direction.
        #lengthToe = 100    #mm Distance from ankle joint to toe in the horizontal direction.
        h = self.decoderFile[:,1]*np.pi/180
        k = self.decoderFile[:,2]*np.pi/180
        a = self.decoderFile[:,3]*np.pi/180
        self.heel[:,0] = yp4*cos(a + h + k) + xp4*sin(a + h + k) + l1*sin(h) + l2*sin(h + k)
        self.heel[:,1] = yp4*sin(a + h +k) - xp4*cos(a + h + k) - l1*cos(h) - l2*cos(h + k)

    def rTrainTestbyGait(self):
    # Summary: self.rAllJointByGait contains the r values in all gaits.
    #          This function splits it into training and testing parts.
    #          The first 60 sec in training is cut away because there wasn't any trained decoder at that time.

    # Prerequisit: readConductor(), gaitSegmentation(), RValueByGaitAllJoint()
    # Input: None
    # Output: rTrain & rTest: 7 columns. The first one is time. The rest are right hip, right knee, right ankle, left hip, l knee, l ankle. Row number equals to the number of gaits/
    #         rTrainMean, rTrainMedian, rTestMean, rTestMedian are all 6 column vectors. the mean/median r value across all gait cycles.

    # Date: 2017/12/12
        self.rTrain = cutArray(self.rAllJointByGait, self.events['tdmStart']+60, self.events['brainStart']-2)
        self.rTest  = cutArray(self.rAllJointByGait, self.events['brainStart']+2, self.events['brainEnd']-5)
        self.rTrainMean = np.nanmean(self.rTrain, axis=0)[1:,]
        self.rTestMean = np.nanmean(self.rTest, axis=0)[1:,]
        self.rTrainMedian = np.nanmedian(self.rTrain, axis=0)[1:,]
        self.rTestMedian = np.nanmedian(self.rTest, axis=0)[1:,]
