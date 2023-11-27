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

    
    def __init__(self, relativePath, figureName):
        # Create dir path and load images
        # Move up two levels to the root directory
        self.figureName = figureName
        self.rootPath = os.path.dirname(os.path.dirname(__file__)) 
        self.fullPath = os.path.join(self.rootPath, 'data', relativePath)
        # self.fullPath = os.path.join(self.absPath, relativePath)
        self.fitsLoader = loadImage.fitsLoader(self.fullPath)
        self.fitsLoader.loadImages()
        
        # Output path for figures
        self.outputDir = os.path.join(os.path.dirname(__file__), '..', 'plots', 'ron_plots')
        self.plotPath = os.path.join(self.outputDir, f'{figureName}.png')



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
        self.subArray = self.stackedArray.astype(np.float32) - self.meanBias.astype(np.float32) 
        # Calc std of subtracted frames
        self.stdArray = np.std(self.subArray, axis = 0)
        self.stdArray /= np.sqrt(2) 
        # self.stdArray = np.mean(self.subArray, axis = 0)
        # self.stdArray = np.sqrt(self.subArray, axis = 0)
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
        
        plt.savefig(self.plotPath)
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

    def marginOfError(self, zScore=1.96, n=545):
        
        self.calcRON()
        std = np.mean(np.sqrt(self.clipped))
        MOE = np.sqrt((zScore**2 * std**2) / n)
        MOE /= np.mean(self.clipped) 
        print(MOE) 