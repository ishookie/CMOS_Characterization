import matplotlib.pyplot as plt
import numpy as np
import os
import sys
sys.path.append("..")
import loadImage

class RON:
    # Sigma Threshold for sigma clipping 
    threshold = 3 

    
    def __init__(self, relativePath):
        # Create dir path and load images
        self.absPath = os.path.dirname(__file__)
        self.fullPath = os.path.join(self.absPath, relativePath)
        self.fitsLoader = loadImage.fitsLoader(self.fullPath)
        self.fitsLoader.loadImages()


    def calcPixelWiseSTD(self):
        """
        Calculates the pixel wise standard deviation across N images
        Returns a 2D numpy array containing the pixel wise STD values
        called stdArray
        """
        self.stackedArray = np.stack(self.fitsLoader.images, axis = 0)
        self.stdArray = np.std(self.stackedArray, axis = 0)


    def plotStatistics(self):
        """
        Prints: Min, Max and Mean values.
        Creates a histogram of RMS pixel values vs log(count)
        array = array to be plotted
        """                
        print(f"Min Value: {np.min(self.clippedData)}")
        print(f"Max Value: {np.max(self.clippedData)}")
        print(f"Mean Value: {np.mean(self.clippedData)}")

        stdArray_flat = self.clippedData.flatten()
        plt.hist(stdArray_flat, bins=100)
        plt.title('RMS Histogram')
        plt.xlabel('RMS Values (ADU)')
        plt.ylabel('log(count)')
        plt.yscale('log')
        plt.show() 
        
        # # Create a heatmap (not really usefull tbh but leaving in) 
        # heatmap = ax1.imshow(array, cmap='jet', aspect='auto')
        # ax1.set_title('RMS Heatmap')
        # plt.colorbar(heatmap, ax=ax1)
        

    def calcRON(self):
        """
        Calculate RON of pixels and plot the statistics
        """
        self.calcPixelWiseSTD() 
        self.sigmaClip() 
        self.plotStatistics() 


    def sigmaClip(self):
        """
        Performs sigma clipping on a np array.
        clipped Data is stored in clippedData
        threshold variable defines the clipping by default is 3
        """
        self.mean = np.mean(self.stdArray)
        self.std = np.std(self.stdArray)
        self.mask = np.abs(self.stdArray - self.mean) < self.threshold*self.std
        self.clippedData = self.stdArray[self.mask] 
