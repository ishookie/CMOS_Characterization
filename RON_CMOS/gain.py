import matplotlib.pyplot as plt 
import numpy as np 
import os 
import math 

import sys
sys.path.append("..")
import loadImage

class GAIN: 

    def __init__(self, relativePathLight, relativePathDark):
        # Create dir path and load images
        self.absPathLight = os.path.dirname(__file__)
        self.fullPathLight = os.path.join(self.absPathLight, relativePathLight)
        self.fitsLoaderLight = loadImage.fitsLoader(self.fullPathLight)
        self.fitsLoaderLight.loadImages()

        self.absPathDark = os.path.dirname(__file__)
        self.fullPathDark = os.path.join(self.absPathDark, relativePathDark)
        self.fitsLoaderDark = loadImage.fitsLoader(self.fullPathDark)
        self.fitsLoaderDark.loadImages() 

        self.resArray = []
        self.sumArray = []
        self.diffArray = []
        self.meanVals = []
        self.varVals = []

    def resFrame(self): 

        for n in range(len(self.fitsLoaderLight.images)):
            self.resArray.append(self.fitsLoaderLight.images[n].astype(np.int32) - self.fitsLoaderDark.images[n].astype(np.int32))
        print(f"resFrame: {self.resArray[0][:5,:5]}")

    def sumFrame(self):
        for n in range(0, len(self.resArray)-1, 2):
            self.sumArray.append((self.resArray[n] + self.resArray[n+1])/2) 
        print(f"sumFrame: {self.sumArray[0][:5,:5]}")

    def diffFrame(self):
        for n in range(0, len(self.resArray) - 1, 2):
            self.diffArray.append(self.resArray[n] - self.resArray[n+1]) 
        print(f"diffArray: {self.diffArray[0][:5,:5]}")

    def calcMean(self):
        for n in self.sumArray:
            self.meanVals.append(np.mean(n))
    
    def calcVariance(self):
        for n in self.diffArray:
            self.varVals.append(np.var(n))


    def doTheThing(self):
        self.resFrame()
        self.diffFrame()
        self.sumFrame() 
        self.calcMean()
        self.calcVariance() 
        self.plotPTC() 


    def plotPTC(self):
        
        print(f"Mean Values: {self.meanVals}")
        slope, intercept = np.polyfit(self.meanVals, self.varVals, 1)
 
        # Super scuffed linear fit line (just a bunch of tightly grouped points)
        bestFit = np.poly1d([slope, intercept])
        x_line = np.linspace(min(self.meanVals), max(self.meanVals), 1000)
        y_line = bestFit(x_line)

        # Plot data points and line of best fit
        plt.scatter(self.meanVals, self.varVals, label='Data Points')
        plt.scatter(x_line, y_line, color='red', label=f'Fit: y = {slope:.2f}x + {intercept:.2f}', s=0.1)

        # Print gain which is 1/slope 
        gain = 1/slope 
        print(f"gain: {gain}")

        # Show the plot
        plt.legend() 
        plt.show()
        

    # def calcDiff(self):
    #     print(self.fitsLoader.images[1].shape)
    #     self.diff = self.fitsLoader.images[1].astype(np.int32) - self.fitsLoader.images[2].astype(np.int32)
    #     print(self.diff[:5,:5]) 

    # def calcVariance(self):
    #     self.subFrame = self.diff[1004:1204, 1508:1709]
    #     self.variance = (np.std(self.subFrame))/math.sqrt(2) 
        
    #     #self.variance = (np.std(self.diff))/math.sqrt(2) 

    # def calcCorrected(self) :
    #     # flat
    #     self.corr = self.fitsLoader.images[1].astype(np.int32) - self.fitsLoader.images[0].astype(np.int32) 
    #     self.mean = np.mean(self.corr[1004:1204, 1508:1709]) 
    #     print(f"Corrected: {self.corr[:5,:5]}")
    
    # def calcGain(self):
    #     self.calcDiff() 
    #     self.calcVariance()
    #     self.calcCorrected()
    #     return self.mean/self.variance