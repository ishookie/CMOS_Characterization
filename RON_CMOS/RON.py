import matplotlib.pyplot as plt
import numpy as np
import os
import sys

from scipy.stats import sigmaclip 

sys.path.append("..")
import loadImage

class RON:
    # Sigma Threshold for sigma clipping 
    threshold = 10

    
    def __init__(self, relativePath):
        # Create dir path and load images
        self.absPath = os.path.dirname(__file__)
        self.fullPath = os.path.join(self.absPath, relativePath)
        self.fitsLoader = loadImage.fitsLoader(self.fullPath)
        self.fitsLoader.loadImages()


    def calcRON(self):
        """
        Calculates the pixel wise standard deviation across N images
        First subtracts individual frames from the mean values of N frames
        Then calculates the std and clips outliers using sigma clipping
        with threshold defined as a class variable
        """
        # Stack frames, subtract individual pixels from mean
        self.stackedArray = np.stack(self.fitsLoader.images, axis = 0)
        self.meanBias = np.mean(self.stackedArray, axis=0)
        self.subArray = self.stackedArray - self.meanBias
        # Calc std of subtracted frames
        self.stdArray = np.std(self.subArray, axis = 0)
        # clip data
        self.clipped, _, _ = sigmaclip(self.stdArray, low=self.threshold, high=self.threshold)
        self.plotStatistics()

    def plotStatistics(self):
            """
            Prints: Min, Max and Mean values.
            Creates a histogram of RMS pixel values vs log(count)
            array = array to be plotted
            """                
            print(f"Min Value: {np.min(self.clipped)}")
            print(f"Max Value: {np.max(self.clipped)}")
            print(f"Mean Value: {np.mean(self.clipped)}")

            stdArray_flat = self.clipped.flatten()
            plt.hist(stdArray_flat, bins=100)
            plt.title('RON Histogram')
            plt.xlabel('RON Values (ADU)')
            plt.ylabel('log(count)')
            plt.yscale('log')
            plt.show() 

            # # Create a heatmap (not really usefull tbh but leaving in) 
            # heatmap = ax1.imshow(array, cmap='jet', aspect='auto')
            # ax1.set_title('RMS Heatmap')
            # plt.colorbar(heatmap, ax=ax1)

    def sampleSize(self, zScore=1.96, MOE=0.02):
        """"
        Calculate the required sample size (n) for a given confidence interval
        and margin of error (MOE) default values:
        CI = 1.96 (95%)
        MOE = 2% 
        """
        self.calcRON()
        std = np.mean(np.sqrt(self.clipped))
        MOE *= np.mean(self.clipped)
        n = (zScore**2 * std**2) / MOE**2 
        print(n) 