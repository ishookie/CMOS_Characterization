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
        self.diff = self.fitsLoader.images[1] - self.fitsLoader.images[2]
        print(self.dsiff) 
    def calcVariance(self):
        self.subFrame = self.diff[502:602, 754:854]
        self.variance = (np.std(self.subFrame))/math.sqrt(2) 

    def calcCorrected(self) :
        # flat
        self.corr = self.fitsLoader.images[1] - self.fitsLoader.images[0] 
        self.mean = np.mean(self.corr) 
    
    def calcGain(self):
        self.calcDiff() 
        self.calcVariance()
        self.calcCorrected()
        return self.mean/self.variance