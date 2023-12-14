import matplotlib.pyplot as plt 
import numpy as np 
import os 
import math 

import sys
sys.path.append("..")
import loadImage

sys.path.append("../cam")
from camera import DLAPICamera
from gateway import DLAPIGateway
from cam import camera, gateway

class GAIN: 

    def __init__(self, relativePathFlat=None, relativePathDark=None, figureName='GRAHAHAHAHAHAHAHAHH_500_0.65s'):
        self.rootPath = os.path.dirname(os.path.dirname(__file__))
        
        self.roiSize = 500
        
        # # Load light images
        # self.fullPathFlat = os.path.join(self.rootPath, 'data', relativePathFlat)
        # self.fitsLoaderFlat = loadImage.fitsLoader(self.fullPathFlat) 
        # self.fitsLoaderFlat.loadImages() 
        # # Load dark images
        # self.fullPathDark = os.path.join(self.rootPath, 'data', relativePathDark)
        # self.fitsLoaderDark = loadImage.fitsLoader(self.fullPathDark)
        # self.fitsLoaderDark.loadImages() 
        # Lists to store data
        # Output path for figures
        self.outputDir = os.path.join(os.path.dirname(__file__), '..', 'plots', 'gain_plots')
        self.plotPath = os.path.join(self.outputDir, f'{figureName}_PTC.png')


    def takeFlats(self, temp, expTime, number = 1, readout_mode = "High Gain"): 
        # """
        # Take a flat. Manually adjust illumination levels of setup and re run this method. 

        # Args:
        #     temp (int): Temperature of sensor in Celcius. 
        #     expTime (int): Exposure time in seconds. 
        #     number (int, optional): number of frames to take. Defaults to 1.
        #     readout_mode (str, optional): Readout mode of sensor. Defaults to "High Gain".
        # """
                # Create new directory for given temperature
        savedir = os.path.join(self.rootPath, 'data', 'gain', 'flat', f"{str(temp)}C", f"{str(expTime)}s")
        if not os.path.exists(savedir):
            os.makedirs(savedir)
            hgPath = os.path.join(savedir, "High Gain")
            lgPath = os.path.join(savedir, "Low Gain")
            os.makedirs(hgPath)
            os.makedirs(lgPath)
        else: 
            hgPath = os.path.join(savedir, "High Gain")
            lgPath = os.path.join(savedir, "Low Gain")
            
        
        # high/low gain adjust save directory 
        if readout_mode == "High Gain":
            savedir = hgPath
        elif readout_mode == "Low Gain": 
            savedir = lgPath
        else:
            print(f"Incorrect readout mode: {readout_mode}")
            return        
        # Create camera objectsss
        gateway = DLAPIGateway() 
        print(f"Images saved to: {savedir}")
        cam = DLAPICamera(gateway, model='stc', dirname=savedir)
        cam.connect()
        # Camera set point
        cam.set_temperature(temp)
        cam.start_cooling()
        # Take Biases
        for n in range(number): 
            result = cam.expose(imtype='flat', readout_mode=readout_mode, exptime=float(expTime))
            # Check if exposure failed
            if "Error." in result.description:
                print(result.description)
                return
            
            
    def takeDarks(self, temp, expTime, number = 10, readout_mode = "High Gain"): 
                # Create new directory for given temperature
        savedir = os.path.join(self.rootPath, 'data', 'gain', 'dark', f"{str(temp)}C", f"{str(expTime)}s")
        if not os.path.exists(savedir):
            os.makedirs(savedir)
            hgPath = os.path.join(savedir, "High Gain")
            lgPath = os.path.join(savedir, "Low Gain")
            os.makedirs(hgPath)
            os.makedirs(lgPath)
        else: 
            hgPath = os.path.join(savedir, "High Gain")
            lgPath = os.path.join(savedir, "Low Gain")
            
        
        # high/low gain adjust save directory 
        if readout_mode == "High Gain":
            savedir = hgPath
        elif readout_mode == "Low Gain": 
            savedir = lgPath
        else:
            print(f"Incorrect readout mode: {readout_mode}")
            return        
        # Create camera objectsss
        gateway = DLAPIGateway() 
        print(f"Images saved to: {savedir}")
        cam = DLAPICamera(gateway, model='stc', dirname=savedir)
        cam.connect() 
        # Camera set point
        cam.set_temperature(temp)
        cam.start_cooling()
        # Take Biases
        for n in range(number): 
            result = cam.expose(imtype='dark', readout_mode=readout_mode, exptime=float(expTime), filename=f"{temp}Cdark_{readout_mode}-{n}.fits")
            # Check if exposure failed
            if "Error." in result.description:
                print(result.description)
                return

    def midROI(self, fitsLoader): 
        """ 
        Grabs the X and Y index for the centermost 300x300 region of a frame
        startX, startY
        endX, endY 
        """
        width = fitsLoader.getHeaderInfo('NAXIS1')
        height = fitsLoader.getHeaderInfo('NAXIS2')     
        self.startX = (width - self.roiSize) // 2
        self.startY = (height - self.roiSize) // 2
        self.endX = self.startX + self.roiSize 
        self.endY = self.startY + self.roiSize
        
#---------------------------TRY NUMBER 3----------------------------------------------------
#               Take flats - same exp time different levels
#               Take corresponding darks - same exposure time
#               Subtract darks from each flat and find variance and mean

    def calcPTC(self, temp=-5, expTime=0.07, readout_mode='High Gain'):
        """_summary_÷
        """
        # Load darks
        darkPath = os.path.join(self.rootPath, 'data', 'gain', 'dark', f"{str(temp)}C", f"{str(expTime)}s", readout_mode)        
        darkLoader = loadImage.fitsLoader(darkPath)
        darks = darkLoader.loadImages()
        
        #Calculate Midpoint 
        self.midROI(darkLoader)
        
        # Load Flats
        flatPath = os.path.join(self.rootPath, 'data', 'gain', 'flat', f"{str(temp)}C", f"{str(expTime)}s", readout_mode)
        flatLoader = loadImage.fitsLoader(flatPath)
        flats = flatLoader.loadImages() 
        
        # Create master dark 
        masterDark = np.stack(darks, axis=0)
        masterDark = np.mean(masterDark, axis=0)
        
        meanVals = []
        varVals = []
       
        for frame in flats:
            subFrame = frame - masterDark     
            # Get region of interest within frame
            ROI = subFrame[self.startX:self.endX, self.startY:self.endY]

            # Calc mean and variance
            mean = np.mean(ROI)
            variance = np.var(ROI)
            meanVals.append(mean) 
            varVals.append(variance) 

        self.plotPTC(meanVals, varVals) 
        
    

    def plotPTC(self, meanVals, varVals):
        """
        Plots the photon transfer curve 
        """
        slope, intercept = np.polyfit(meanVals, varVals, 1)
        # Super scuffed linear fit line (just a bunch of tightly grouped points)
        bestFit = np.poly1d([slope, intercept])
        x_line = np.linspace(min(meanVals), max(meanVals), 1000)
        y_line = bestFit(x_line)
        # Plot data points and line of best fit
        plt.scatter(meanVals, varVals)
        
        # Gain is 1/slope and RON is sqrt(y-intercept)
        gain = 1/slope
        ron = math.sqrt(abs(intercept))
        print(f"Gain: {gain:.2f} RON: {ron:.2f}")
        # Graph PTC
        plt.scatter(x_line, y_line, color='red', label=f'Gain: {gain:.2f} RON: {ron:.2f}', s=0.1)
        plt.xlabel("Mean")
        plt.ylabel("Variance")
        # Show and save the plot
        plt.title("Photon Transfer Curve")
        plt.legend()
        plt.savefig(self.plotPath) 
        plt.show()


    def spacialVariation(self): 
        """
        AHHH WHAT DOES THIS DO ITS IN MY BRAIN
        """
        #Create Master Dark 
        masterDark = np.stack(self.fitsLoaderDark.images, axis=0)
        masterDark = np.mean(masterDark, axis=0)

        ### ADD THE LOOP HERE 48 box size
        gainVals = []

        for x in range(0, 3216, 48):
            for y in range(0, 2208, 48):
                
                meanNums = []
                varNums = [] 

                for frame in self.fitsLoaderFlat.images:
                    subFrame = frame - masterDark     
                    # get region of interest within frame
                    ROI = subFrame[x:x+48, y:y+48]
                    mean = np.mean(ROI)
                    variance = np.var(ROI)

                    meanNums.append(mean) 
                    varNums.append(variance)

                gain, intercept = np.polyfit(meanNums, varNums, 1)

                gainValues.append(gain) 


        original = np.zeros((3216, 2208))

        # Reshape frame with 48x48 binning
        gainValues = np.array(gainValues).reshape(3216 // 48, 2208 // 48)

        for i in range(67):
            for j in range(46):
                original[i*48:(i+1)*48, j*48:(j+1)*48] = gainValues[i,j]
        
        plt.imshow(original, cmap='viridis', origin='lower', aspect='auto')
        plt.colorbar(label='Gain Value')
        plt.title("Gain Values Heatmap")
        plt.show() 

    def printKeyandVals(self, imageList):
        """
        Debugging function 
        Given a dictionary of images
        Print the key and number of values associated with that key
        """
        for key, value in imageList.items():
            print(f"Key: {key}, num of Values: {len(value)}")

    
    def gcd(self):
        """
        Helper function to find greatest common square size for a nxm image
        Throws exception if result is not an integer value
        """
        height, width = np.shape(self.fitsLoaderFlat.images[0])
        gcd = math.gcd(width, height)
        if not isinstance(gcd, int):
            raise ValueError("Square Size is not an Integer")
        print(gcd)
        return gcd
    
    def readoutTest(self):
        savedir = os.path.join(self.rootPath, 'data', 'gain')
        gateway = DLAPIGateway() 
        print(f"Images saved to: {savedir}")
        cam = DLAPICamera(gateway, model='stc', dirname=savedir)
        cam.connect() 
        res = cam.get_readout_modes()
        print(res.payload) 
        
