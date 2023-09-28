import loadImage 
import numpy as np 
import math 
import os 
import sys
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

sys.path.append("..")
import loadImage

class DC: 
    def __init__(self, relativePath):
        # Create dir path and load iamges
        self.absPath = os.path.dirname(__file__)
        self.fullPath = os.path.join(self.absPath, relativePath)
        self.fitsLoader = loadImage.fitsLoader(self.fullPath)
        # Load images with exposure time as key -> keyImages
        self.fitsLoader.sortImages('EXPTIME')
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
            
            if expTime not in self.diffDict:
                self.diffDict[expTime] = []
            
            self.diffDict[expTime].append(diff) 
            # FIX THIS PLEASE
            # Calc dark current here - using 1.2 as stock gain value
            self.darkCurrents[expTime] = (1.2 * np.var(diff)) / expTime 


    def graphDCvsTIME(self):
        
        
        times = list(self.darkCurrents.keys())
        values = list(self.darkCurrents.values())

        print(f"Times: {times}")
        print(f"Values: {values}")
        

        values = np.array(values)
        times = np.array(times)

       # Fit a logarithmic function
        params = np.polyfit(np.log(times), values, 1)
        a, b = params

        # Scatter plot of the data points
        plt.scatter(times, values, label='Dark Current vs Time', color='blue')

        # Generate the fitted curve
        fittedCurve = a * np.log(times) + b

        # Plot the fitted curve
        plt.plot(times, fittedCurve, 'r--', label='Logarithmic Fit')

        plt.xlabel('Time (s)')
        plt.ylabel('Dark Current (e-)')
        plt.grid(True)
        plt.legend()
        plt.show()




