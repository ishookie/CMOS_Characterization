import loadImage 
from astrpopy.io import fits
import numpy as np 
import math 
import os 
import RON

import sys
sys.path.append("..")
import loadImage

class DC: 
    
    def __init__(self, relativePath):
        # Create dir path and load iamges
        self.absPath = os.path.dirname(__file__)
        self.fullPath = os.path.join(self.absPath, relativePath)
        self.fitsLoader = loadImage.fitsLoader(self.fullPath)
        self.fitsLoader.loadImages()
        

    def stackFrame(self, ronAvg , t): 
        stackedFrame = np.std(self.fitsLoader.images[0] - self.fitsLoader.images[1])
        final = ((stackedFrame/math.sqrt(2))**2 - (ronAvg)**2) / t
        
        
