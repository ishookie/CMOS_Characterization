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
    def __init__(self, relativePath, biasPath = '-5.0C_highGain'):
        # Create dir path and load iamges
        self.absPath = os.path.dirname(__file__)
        self.fullPath = os.path.join(self.absPath, '..', 'frames', relativePath)
        self.fitsLoader = loadImage.fitsLoader(self.fullPath)
        # Load images with exposure time as key -> keyImages
        self.fitsLoader.sortImages('EXPTIME')
        self.diffDict = {} 
        self.darkCurrents = {}
        self.diff = [] 
        # Load bias to create master bias 
        self.fullPathBias = os.path.join(self.absPath, '..', 'frames', biasPath)
        self.fitsLoaderBias = loadImage.fitsLoader(self.fullPathBias)
        self.fitsLoaderBias.loadImages()


    def fullFrameDC(self):
        """
        Test to calculate the dark current vs time for the entire image. 
        """
        #Create master bais 
        masterBias = np.stack(self.fitsLoaderBias.images, axis=0)
        masterBias = np.mean(masterBias)

        for expTime, dataList in self.fitsLoader.keyImages.items(): 
            stackedFrame = np.stack(dataList, axis=0)
            dc = np.mean(stackedFrame)
            # Subtract Bias from dark frames
            dc = dc - masterBias
            
            if expTime not in self.darkCurrents:
                self.darkCurrents[expTime] = []
            self.darkCurrents[expTime] = dc 
   

    def graphDCvsTIME(self):
        """
        Plot Dark Current Count vs Time
        Also display Dark Current (slope of linear fit)
        """
        # Load Times and Values
        times = list(self.darkCurrents.keys())
        values = list(self.darkCurrents.values())
        values = np.array(values)
        times = np.array(times)
        # Fit a linear function
        params = np.polyfit(times, values, 1)
        a, b = params
        # Scatter plot of the data points
        plt.scatter(times, values, label='Dark Current vs Time', color='blue')
        # Annotate each point with its dark current value
        for i, txt in enumerate(values):
            plt.annotate(f'{txt:.2f}', (times[i], values[i]), textcoords="offset points", xytext=(0, 10), ha='center')
        # Create the linear fit equation text
        equation_text = f'Dark Current: {a:.2f} e-/p/s'
        # Print DC value
        print(f"Dark Current: {a:.2f} e-/p/s")
        # Also put DC value on graph
        plt.text(0.1, 0.9, equation_text, transform=plt.gca().transAxes, fontsize=12, bbox=dict(facecolor='white', edgecolor='black'))
        # Title the graph
        plt.title('Dark Current vs Time')
        # Generate the fitted curve
        fittedCurve = a * times + b
        # Plot the fitted curve
        plt.plot(times, fittedCurve, 'r--', label='Linear Fit')
        #Label and show graph 
        plt.xlabel('Time (s)')
        plt.ylabel('Dark Current (e-)')
        plt.grid(True)
        plt.show()




