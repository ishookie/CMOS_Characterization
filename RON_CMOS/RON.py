import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.visualization import astropy_mpl_style
import numpy as np
import math
import os

import sys
sys.path.append("..")
import loadImage

class RON:
    total = 0
    pixelArray = np.empty(100, dtype=np.int32) 

    # Sigma Threshold for sigma clipping 
    threshold = 3 

    
    """
    Initialize class -> load images frome specified folder called "relativePath" 
    """
    def __init__(self, relativePath):
        # Create dir path and load images
        self.absPath = os.path.dirname(__file__)
        self.fullPath = os.path.join(self.absPath, relativePath)
        self.fitsLoader = loadImage.fitsLoader(self.fullPath)
        self.fitsLoader.loadImages()
        self.stdArray = np.empty_like(self.fitsLoader.images[0], dtype=np.float64)
        # length = len(self.fitsLoader.images)
        # self.pixelArray = np.empty(length, dtype=np.int32) 


    """
    returns a 1D array of length N
    Contains the pixel value at a (x,y) coordinate for N frames
    """
    def retrievePixels(self, x, y):
        for i, img in enumerate(self.fitsLoader.images):
            newElement = img[y][x]
            self.pixelArray[i] = newElement

    """
    find rms of pixel array
    """
    def calcRMS(self):
        return np.std(self.pixelArray)  


    """
    Calculate RMS of each pixel and store in new array called
    "stdArray" 
    """
    def calcPixelSTD(self):
        rows, cols = self.fitsLoader.images[0].shape
        for y in range(rows - 1):
            for x in range(cols - 1):
                self.retrievePixels(x,y)
                rms = self.calcRMS() 
                self.stdArray[y][x] = rms 
    
    """
    Prints the: min, max and mean values
    Creates a heatmap of RMS pixel values
    Creates a histogram of RMS pixel values vs log(count) 
    array = array to be plotted
    """
    def plotStatistics(self, array):
        
        print(f"Min Value: {np.min(array)}")
        print(f"Max Value: {np.max(array)}")
        print(f"Mean Value: {np.mean(array)}")

        fig, (ax1, ax2) = plt.subplots(1,2, figsize=(10,5))

        # # Creat a heatmap 
        # heatmap = ax1.imshow(array, cmap='jet', aspect='auto')
        # ax1.set_title('RMS Heatmap')
        # plt.colorbar(heatmap, ax=ax1)

        stdArray_flat = array.flatten()
        #create
        ax2.hist(stdArray_flat, bins=100)
        ax2.set_title('RMS Histogram')
        ax2.set_xlabel('RMS Values (ADU)')
        ax2.set_ylabel('log(count)')
        ax2.set_yscale('log')

        plt.tight_layout()
        plt.show() 
        
    """
    Calculate RON of pixels and plot the statistics
    """
    def calcRON(self):
        self.calcPixelSTD()
        self.sigmaClip() 
        #self.plotStatistics() 

    def sigmaClip(self):
        self.mean = np.mean(self.stdArray)
        self.std = np.std(self.stdArray)
        self.mask = np.abs(self.stdArray - self.mean) < self.threshold*self.std
        self.clippedData = self.stdArray[self.mask] 
        print(self.clippedData.shape)