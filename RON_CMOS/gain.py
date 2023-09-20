import matplotlib.pyplot as plt 
import numpy as np 
import os 
import math 

import sys
sys.path.append("..")
import loadImage

class GAIN: 

    def __init__(self, relativePath):
        # Create dir path and load images
        self.absPath = os.path.dirname(__file__)
        self.fullPath = os.path.join(self.absPath, relativePath)
        self.fitsLoader = loadImage.fitsLoader(self.fullPath)
        self.fitsLoader.loadImages()
        self.stdArray = np.empty_like(self.fitsLoader.images[0], dtype=np.float64)


    def calcDiff(self):
        print(self.fitsLoader.images[1].shape)
        self.diff = self.fitsLoader.images[1].astype(np.int32) - self.fitsLoader.images[2].astype(np.int32)
        print(self.diff[:5,:5]) 

    def calcVariance(self):
        self.subFrame = self.diff[1004:1204, 1508:1709]
        self.variance = (np.std(self.subFrame))/math.sqrt(2) 
        
        #self.variance = (np.std(self.diff))/math.sqrt(2) 

    def calcCorrected(self) :
        # flat
        self.corr = self.fitsLoader.images[1].astype(np.int32) - self.fitsLoader.images[0].astype(np.int32) 
        self.mean = np.mean(self.corr[1004:1204, 1508:1709]) 
        print(f"Corrected: {self.corr[:5,:5]}")
    
    def calcGain(self):
        self.calcDiff() 
        self.calcVariance()
        self.calcCorrected()
        return self.mean/self.variance