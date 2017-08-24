# Trial object is all information in one trial. Each subject should have 8 trials (4 days * 2 per day)
import os
import numpy as np
import mne
import matplotlib.pyplot as plt
from detect_peaks import detect_peaks
from asp.spectrogram import spectrogram_timewrap
from asp.rolling_r_value import rolling_r_value  # a small function to compute rolling r value
import statsmodels.api as sm  # for some reason also need to install patsy
from numpy import cos, sin, pi

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
    fs = 100
    eegFile = -1  # raw eeg file
    decoderFile = -1  # raw decoder file
    conductorFile = -1  # raw conductor file
    impedanceBefore = -1
    impedanceAfter = -1
    # locationFile = -1 # 60Ch_EOGlayout.locs
    impedanceRemove = -1
    info = -1
    gaitSegments_rmOutliers = -1 # gait cycles. each row contains the starting and ending time of one cycle
    gaitSpecgramMean = -1
    gaitSpecgramMeanFreqs = -1
    rCurveHip = -1 # regressed curve of the windowed r values
    rCurveKnee = -1 
    rCurveAnkle = -1
    heel = -1 # trajectory of the heel in sagittal plane. 
    events = -1 # a dict with four times: treadmill starts, brain control starts, brain control ends, treadmill ends 

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
        readMontage = mne.channels.read_montage(kind='60Ch_EOGlayout', path='resources/')
        self.info = mne.create_info(readMontage.ch_names, self.fs, ch_types='eeg', montage=readMontage)


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
        
        
    def fitRcurve(self, joint):
    # Summary: fit a curve of the windowed r values in a trial
    # Prerequisit: t.events
    # Input: joint is a string of either 'hip', 'knee', or 'ankle'
    # Output: The returned array (such as rCurveHip) is two-dimensional array. The first column contains time in minutes, and the second column the associated estimated y values.
    # Date: 
        try:
            joint=='hip' or joint=='knee' or joint=='ankle'
        except ValueError:
            print 'Wrong joint to fit r curve.'
                
        if joint=='hip':
            jointId = 0
        elif joint=='knee':
            jointId = 1
        elif joint=='ankle':
            jointId = 2
        
        winLen = 1000
        r_fs = 500
        r = rolling_r_value(self.decoderFile[:,1+jointId], self.decoderFile[:,7+jointId], winLen, r_fs)
        r_time = self.decoderFile[0:-winLen:r_fs, 0].copy() - self.events['brainStart']
        #pick a sample every r_fs samples

        # curve fitting
        if joint=='hip': 
            self.rCurveHip = sm.nonparametric.lowess(r, r_time/60.0, frac=0.3)
        if joint=='knee': 
            self.rCurveKnee = sm.nonparametric.lowess(r, r_time/60.0, frac=0.3)
        if joint=='ankle': 
            self.rCurveAnkle = sm.nonparametric.lowess(r, r_time/60.0, frac=0.3)
            
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
        
        
        
        
        
        
        
        
        
        
        
        
        