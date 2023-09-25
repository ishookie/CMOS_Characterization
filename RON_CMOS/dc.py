import loadImage 
import numpy as np 
import math 
import os 
import sys
import matplotlib.pyplot as plt

sys.path.append("..")
import loadImage

"""
take diff frames D0 - D1 + D2 - D3.......
calc cariance of diff frames
-> do this with a bumch of exp times (object for each)
-> graph accordingly 

"""

class DC: 
    def __init__(self, relativePath):
        # Create dir path and load iamges
        self.absPath = os.path.dirname(__file__)
        self.fullPath = os.path.join(self.absPath, relativePath)
        self.fitsLoader = loadImage.fitsLoader(self.fullPath)
        self.fitsLoader.loadImages()
        self.t = round(self.fitsLoader.getHeaderInfo('EXPTIME'), 0)
        # self.diff = np.empty_like(self.fitsLoader.images[0], dtype=np.float64)

    def diffFrame(self):
        """
        Takes an even number of dark frames "D" and subtracts them following this formula:
        D = D0 - D1 + D2 - D3 + ... + Dn - Dn-1
        """
        for n in range(0, len(self.fitsLoader.images) - 1, 2):
            self.diff += self.fitsLoader.images[n].astype(np.float64) - self.fitsLoader.images[n+1].astype(np.float64)
        self.variance = np.std(self.diff) / math.sqrt(2)

    def stackDarkCurrent(self):
        self.diffFrame() 
        #Quadtrature differnce IM BAD AT STATS THIS IS BAD DONT USE KEEP COMMENTED
        # self.dc = ((1.2 * self.variance)**2 - (1.788**2)) / self.t
        dc = (1.2 * self.variance) / self.t
        print(dc)
        return dc
    
    def logarithmic_fit(self, x, a, b):
        return a * np.log(x) + b

    def graphDCvsTIME(self, data):
        
        values, times = zip(*data) 


        values = np.array(values)
        times = np.array(times)

        print(values)
        print(times)

        params = np.polyfit(np.log(times), values, 1)

        a, b = params  


        plt.scatter(times, values, label='Dark Current vs Time')

        fittedCurve = self.logarithmic_fit(times, a, b)

        plt.plot(times, fittedCurve, color='red', label='logoarithmic Fit')

        plt.xlabel('Time (s)')
        plt.ylabel('Dark Current (e-)')
        plt.legend()

        plt.show() 

        




