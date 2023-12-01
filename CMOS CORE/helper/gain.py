import matplotlib.pyplot as plt 
import numpy as np 
import os 
import math 

import sys
sys.path.append("..")
import loadImage

class GAIN: 

    def __init__(self, relativePathFlat, relativePathDark, figureName):
        self.rootPath = os.path.dirname(os.path.dirname(__file__))
        
        # Load light images
        self.fullPathFlat = os.path.join(self.rootPath, 'data', relativePathFlat)
        self.fitsLoaderFlat = loadImage.fitsLoader(self.fullPathFlat) 
        self.fitsLoaderFlat.loadImages() 
        # Load dark images
        self.fullPathDark = os.path.join(self.rootPath, 'data', relativePathDark)
        self.fitsLoaderDark = loadImage.fitsLoader(self.fullPathDark)
        self.fitsLoaderDark.loadImages() 
        # Lists to store data
        # Output path for figures
        self.outputDir = os.path.join(os.path.dirname(__file__), '..', 'plots', 'gain_plots')
        self.plotPath = os.path.join(self.outputDir, f'{figureName}_PTC.png')


    def midROI(self): 
        """ 
        Grabs the X and Y index for the centermost 300x300 region of a frame
        startX, startY
        endX, endY 
        """
        width = self.fitsLoaderDark.getHeaderInfo('WIDTH')
        height = self.fitsLoaderDark.getHeaderInfo('HEIGHT')
        self.startX = (width - 300) // 2
        self.startY = (height - 300) // 2
        self.endX = self.startX + 300 
        self.endY = self.startY + 300
        
#---------------------------TRY NUMBER 3----------------------------------------------------
#               Take flats - same exp time different levels
#               Take corresponding darks - same exposure time
#               Subtract darks from each flat and find variance and mean

    def calcPTC(self):
        """_summary_
        """
        #Calculate Midpoint 
        self.midROI()
        #Create Master Dark 
        masterDark = np.stack(self.fitsLoaderDark.images, axis=0)
        masterDark = np.mean(masterDark, axis=0)
        
        meanVals = []
        varVals = []
       
        for frame in self.fitsLoaderFlat.images:
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
