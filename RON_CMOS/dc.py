import loadImage 
import numpy as np 
import math 
import os 
import sys
import matplotlib.pyplot as plt

sys.path.append("..")
import loadImage

class DC: 
    def __init__(self, relativePath):
        # Create dir path and load iamges
        self.absPath = os.path.dirname(__file__)
        self.fullPath = os.path.join(self.absPath, relativePath)
        self.fitsLoader = loadImage.fitsLoader(self.fullPath)
        # Load images with exposure time as key -> keyImages
        self.fitsLoader.keyImages('EXPTIME')
        self.diffDict = {} 
        self.darkCurrents = {}

        self.diff = [] 

    def diffFrame(self):
        """
        Takes an even number of dark frames "D" and subtracts them following this formula:
        D = D0 - D1 + D2 - D3 + ... + Dn - Dn-1
        Difference frames are stored in a dictionary with exposure time keys called
        diffDict
        Also calcualtes the overall dark currents with and stores them in a dictionary
        with key values being exposure time
        """
        #Loop through image data for each exposure time key 
        for expTime, dataList in self.fitsLoader.keyImages.items():
            diff = 0 
            #Calcualate difference
            for n in range(0, len(dataList) - 1, 2):
                diff += dataList[n].astype(np.float64) - dataList[n+1].astype(np.float64)
            
            self.diffDict[expTime] = diff 
            # Calc dark current here - using 1.2 as stock gain value
            self.darkCurrents[expTime] = (1.2 * np.var(diff)) / expTime 


    def graphDCvsTIME(self):
        
        values = list(self.darkCurrents.keys())
        times = list(self.darkCurrents.values())
        

        values = np.array(values)
        times = np.array(times)

        print(values)
        print(times)

        params = np.polyfit(np.log(times), values, 1)

        a, b = params  


        plt.scatter(times, values, label='Dark Current vs Time')

        fittedCurve = self.logarithmic_fit(times, a, b)

        plt.xlabel('Time (s)')
        plt.ylabel('Dark Current (e-)')
        plt.grid(True)
        
        coeff, _ = np.polyfit(np.log(times), np.log(values), 1)
        fittedValues = np.exp(coeff[1]) * np.power(times, coeff[0])
        
        plt.plot(times, fittedValues, 'r--', label='logoarithmic Fit')
        
        plt.legend()
        plt.show() 

        
    def logarithmic_fit(self, x, a, b):
        """
        Helper for graphing function - logmarithic fit
        """
        return a * np.log(x) + b



