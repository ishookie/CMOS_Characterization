import sys
import time

# sys.path.append("..")
from helper import gain, dc, ron, linearity, chargePersistence, saltnPepper

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

    
def dcData(temps=[0, -5, -10, -15, -20], times=[1,10,60,120,240]):
    test = dc.DC()
    for temp in temps:
        for t in times:
            test.takeDarks(temp, t)

def processDC():
    test = dc.DC()
    temp1 = 0
    temp2 = -5
    temp3 = -10
    temp4 = -15
    temp5 = -20
    test.fullFrameDC(temp1=temp1, temp2=temp2, temp3=temp3, temp4=temp4, temp5=temp5)
    
#----------------GAIN---------------------------------------------------------------
def takeGainFlats():
    test = gain.GAIN()
    test.takeFlats(temp=-5, expTime=0.065, readout_mode = 'Low Gain')

def takeGainDarks():
    test = gain.GAIN()
    test.takeDarks(temp=-5, expTime=0.065, readout_mode = 'Low Gain')
    
def calcGain():
    test = gain.GAIN()
    test.readoutTest() 
    # test.calcPTC(expTime=0.065, readout_mode='Low Gain')


#----------------LINEARITY---------------------------------------------------------------
def takeLinearityFlats():
    test = linearity.LINEARITY()
    expTimes = [0, 0.01, 0.02, 0.05, 0.1, 0.3, 0.4, 
                0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 
                20, 30, 40, 45, 50, 55,  60, 65, 70, 
                75, 80, 85, 90, 100, 105, 110, 115, 120]
    
    for time in expTimes:
        test.takeFlats(temp=-7, expTime=time)
    
def calcLinearity():
    test = linearity.LINEARITY()
    test.calcCurve(temp=-7)
    

#----------------CHARGE PERSISTENCE---------------------------------------------------------------
def testChargePersistence():
    """
    Takes a light image at saturation then takes 300 biases in 1s intervals immedietly after
    Saved images in data/chargePersistence  
    """
    test = chargePersistence.CHARGEPERSISTENCE(numBias=300, figureName="Charge_Persistence_run2")
    test.takeImages() 
    
def calcChargePersistence(): 
    """
    Calculates charge persistance and saves chart to plots/chargePersistence
    """
    test = chargePersistence.CHARGEPERSISTENCE()
    test.calcPersistence() 

#----------------SALT AND PEPPER---------------------------------------------------------------

def testSaltnPepper():
    """
    Takes n biases and saves them to the saltnPepper data folder. 
    """
    test = saltnPepper.SALTNPEPPER()
    test.takeBias(temp=-5, number=100)

def calcSaltnPepper():
    test = saltnPepper.SALTNPEPPER()
    test.calcSaltnPepper() 

calcSaltnPepper() 
#testSaltnPepper()
