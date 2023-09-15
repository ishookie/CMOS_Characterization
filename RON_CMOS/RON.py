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
    pixelArray = np.empty(10, dtype=np.int32)
    total = 0
    
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


    """
    returns a 1D array of length N
    Contains the pixel value at a (x,y) coordinate for N frames
    """
    def retrievePixels(self, x, y):
        for i, img in enumerate(self.fitsLoader.images):
            newElement = img[y][x]
            self.pixelArray[i] = newElement
        # get rid of this probably 
        # return self.pixelArray 

    """
    find rms of pixel array
    """
    def calcRMS(self):               # Sqrt(N)? - I dont think I need this - uncorrelelated pixels
        return np.std(self.pixelArray) #/ math.sqrt(len(self.pixelArray))  


    """
    Calculate RMS of each pixel and store in new array called
    "stdArray" 
    """
    def calcPixelRMS(self):
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
    """
    def plotStatistics(self):
        
        print(f"Min Value: {np.min(self.stdArray)}")
        print(f"Max Value: {np.max(self.stdArray)}")
        print(f"Mean Value: {(np.sum(self.stdArray))/(np.prod(self.stdArray.shape))}")

        fig, (ax1, ax2) = plt.subplots(1,2, figsize=(10,5))

        # Creat a heatmap 
        heatmap = ax1.imshow(self.stdArray, cmap='jet', aspect='auto')
        ax1.set_title('RMS Heatmap')
        plt.colorbar(heatmap, ax=ax1)

        stdArray_flat = self.stdArray.flatten()
        #create
        ax2.hist(stdArray_flat, bins=200)
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
        self.calcPixelRMS()
        #self.plotStatistics() 


    def subRON(self, x, y): 
        self.subArray = np.empty(5, dtype=np.int32)
        i=0
        
        for n in range(0, len(self.fitsLoader.images) - 1, 2):
            arr = arr = self.fitsLoader.images[n].astype('int32')
            newElement = arr[x][y]
            newElement2 = arr[x][y]
            print(type(newElement))
            print(newElement, newElement2)
            self.subArray[i] = newElement - newElement2
            i += 1
        print(self.subArray)
        # get rid of this probably 
        # return self.pixelArray 

