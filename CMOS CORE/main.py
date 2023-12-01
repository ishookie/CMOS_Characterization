import sys

# sys.path.append("..")
from helper import gain, dc, ron 

def testRON(biasPath, figureName):
    """
    Test RON.
    biasPath (str): where bias frames are ex: bias_frames/high_gain
    figureName (str): Name of output plot. Plots are saved in plots/ron_plots
    """
    ronObject = ron.RON(biasPath, figureName)
    ronObject.calcRON()   

def testGain(flatPath, darkPath):
    test = gain.GAIN(flatPath, darkPath)
    test.spacialVariation()


def testPixelWiseGain(flatPath, darkPath, figureName):
    test = gain.GAIN(flatPath, darkPath, figureName)
    test.calcPTC()

def testDC():
    darkCurrent = dc.DC('dcNew', '-5.0C_highGain')
    darkCurrent.fullFrameDC()
    darkCurrent.graphDCvsTIME()

# testGain('flat_frames/high_gain', 'dark_frames')
# testPixelWiseGain('flat_frames/high_gain', 'dark_frames/high_gain', 'test')
ronObject = ron.RON()
# ronObject.takeData(-5, number=100)

# ronObject.takeData(-5) 
ronObject.createMasterBias(-5) 
# testRON('bias_frames/high_gain', "Clipped_Plot") 

# test = dc.DC() 
# test.takeDarks(-2, 1)
