# Trial object is all information in one trial. Each subject should have 8 trials (4 days * 2 per day)
import os


class Trial:
    filePath = '' # file path of the folder
    subID = -1
    triID = -1
    subIDStr = ''
    triIDStr = ''
    eegFile = -1  # raw eeg file
    decoderFile = -1 # raw decoder file
    conductorFile = -1 # raw conductor file

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
        self.subID = subID;
        self.triID = triID;
        # if SubId<10, add '0' in front to make double digit
        if subID<10:
            self.subIDStr = '0' + str(subID)
        else:
            self.subIDStr = str(subID)
        # same for TriId
        if triID<10:
            self.triIDStr = '0' + str(triID)
        else:
            self.triIDStr = str(triID)
        # file path
        self.filePath = '../Avatar Stroke Data/SS' + self.subIDStr + '-T' + self.triIDStr + '/'
        try:
            os.path.isdir(self.filePath)
        except EnvironmentError:
            print 'No data directory'

        # files
        allFiles = os.listdir(self.filePath)

        print ('sup')

t = Trial(1,2)
