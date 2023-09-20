import loadImage 
import numpy as np 
import math 
import os 
import sys
sys.path.append("..")
import loadImage

class DC: 
    def __init__(self, relativePath, t):
        # Create dir path and load iamges
        self.t = t 
        self.absPath = os.path.dirname(__file__)
        self.fullPath = os.path.join(self.absPath, relativePath)
        self.fitsLoader = loadImage.fitsLoader(self.fullPath)
        self.fitsLoader.loadImages()
        self.diff = np.empty_like(self.fitsLoader.images[0], dtype=np.float64)

    def diffFrame(self):
        for n in range(0, len(self.fitsLoader.images) - 1, 2): #----Finish This for multiple images D0-D1+D2-D3....
            self.diff += self.fitsLoader.images[n].astype(np.float64) - self.fitsLoader.images[n+1].astype(np.float64)
        self.variance = np.std(self.diff) / math.sqrt(2)

    def stackDarkCurrent(self):
        self.diffFrame() 
        # self.dc = ((1.2 * self.variance)**2 - (1.788**2)) / self.t
        self.dc = (1.2 * self.variance) / self.t
        print(self.dc)
        
