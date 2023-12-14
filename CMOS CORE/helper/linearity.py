import matplotlib.pyplot as plt 
import numpy as np 
import os 
import math 

import sys
sys.path.append("..")
import loadImage

sys.path.append("../cam")
from camera import DLAPICamera
from gateway import DLAPIGateway
from cam import camera, gateway

class LINEARITY: 

    def __init__(self, roiSize=500, figureName='LinearityTest_2min'):
        """
        Init for Linearity class. 

        Args:
            roiSize (int, optional): nxn pixel box for linearity calculations. Defaults to 500.
            figureName (str, optional): Name of saved plot. Defaults to 'LinearityTest_2min'.
        """
        self.roiSize = roiSize
        self.rootPath = os.path.dirname(os.path.dirname(__file__))
        self.outputDir = os.path.join(os.path.dirname(__file__), '..', 'plots', 'linearity_plots')
        self.plotPath = os.path.join(self.outputDir, f'{figureName}_Plot.png')


    def takeFlats(self, temp, expTime, number = 1, readout_mode = "High Gain"): 
        """
        Take a flat. Manually adjust illumination levels of setup and re run this method. 

        Args:
            temp (int): Temperature of sensor in Celcius. 
            expTime (int): Exposure time in seconds. 
            number (int, optional): number of frames to take. Defaults to 1.
            readout_mode (str, optional): Readout mode of sensor. Defaults to "High Gain".
        """
        # Create new directory for given temperature
        savedir = os.path.join(self.rootPath, 'data', 'linearity', 'flat', f"{str(temp)}C")
        if not os.path.exists(savedir):
            os.makedirs(savedir)
            hgPath = os.path.join(savedir, "High Gain")
            lgPath = os.path.join(savedir, "Low Gain")
            os.makedirs(hgPath)
            os.makedirs(lgPath)
        else: 
            hgPath = os.path.join(savedir, "High Gain")
            lgPath = os.path.join(savedir, "Low Gain")
            
        # high/low gain adjust save directory 
        if readout_mode == "High Gain":
            savedir = hgPath
        elif readout_mode == "Low Gain": 
            savedir = lgPath
        else:
            print(f"Incorrect readout mode: {readout_mode}")
            return        
        # Create camera objectsss
        gateway = DLAPIGateway() 
        print(f"Images saved to: {savedir}")
        cam = DLAPICamera(gateway, model='stc', dirname=savedir)
        cam.connect()
        # Camera set point
        cam.set_temperature(temp)
        cam.start_cooling()
        # Take Biases
        for n in range(number): 
            result = cam.expose(imtype='flat', readout_mode=readout_mode, exptime=float(expTime), filename=f"{temp}Cflat_{expTime}s_{readout_mode}-{n}.fits")
            # Check if exposure failed
            if "Error." in result.description:
                print(result.description)
                return
            

    def midROI(self, fitsLoader): 
        """ 
        Grabs the X and Y index for the centermost nxn region of a frame
        startX, startY
        endX, endY 
        """
        width = fitsLoader.getHeaderInfo('NAXIS1')
        height = fitsLoader.getHeaderInfo('NAXIS2')     
        self.startX = (width - self.roiSize) // 2
        self.startY = (height - self.roiSize) // 2
        self.endX = self.startX + self.roiSize 
        self.endY = self.startY + self.roiSize
        

    def calcCurve(self, temp=-5, readout_mode='High Gain'):
        """
        Calculates the linearity curve.

        Args:
            temp (int, optional): Temperature of sensor (for loading data). Defaults to -5.
            readout_mode (str, optional): Readout mode of sensor either: "High Gain" or "Low Gain". Defaults to 'High Gain'.
        """
        # Load Flats
        flatPath = os.path.join(self.rootPath, 'data', 'linearity', 'flat', f"{str(temp)}C", readout_mode)
        print(flatPath)
        flatLoader = loadImage.fitsLoader(flatPath)
        flats = flatLoader.sortImages('EXPTIME') 
        
        # Calc mean vals 
        expTimeVals = []
        meanVals = []
        for t, frame in flats.items():
            expTimeVals.append(t)
            meanVal = np.mean(frame)
            meanVals.append(meanVal)
        
        print(f"mean: {meanVals}")
        print(f"expTime: {expTimeVals}")
        self.plotCurve(expTimeVals, meanVals) 
        

    def plotCurve(self, expTimeVals, meanVals):
        """
        Plot linearity curve and save figure to:
        plots/linearity

        Args:
            expTimeVals (list): list of exposure time values. 
            meanVals (list): List of mean values of frames.
        """
        # Filter data to exclude values over 4000 from the linear fit
        filtered_data = [(t, m) for t, m in zip(expTimeVals, meanVals) if m <= 4050]
        x_data_fit, y_data_fit = zip(*filtered_data)
        # Convert lists to numpy arrays for linear regression
        x_data_fit = np.array(x_data_fit)
        y_data_fit = np.array(y_data_fit)
        # Get Linear fit
        slope, intercept = np.polyfit(x_data_fit, y_data_fit, 1)
        # Generate linear fit line
        fit_line = slope * x_data_fit + intercept
        # Plot the data and linear fit
        plt.scatter(expTimeVals, meanVals, label='Saturated Values')
        plt.scatter(x_data_fit, y_data_fit, color='red', label='Data Before Saturation')
        plt.plot(x_data_fit, fit_line, color='red', linestyle='--', label=f'Linear Fit: y = {slope:.2f}x + {intercept:.2f}')
        # Add labels and title
        plt.xlabel('Exposure Time (seconds)')
        plt.ylabel('Mean ADU')
        plt.title('Linearity')
        # Add legend
        plt.legend()
        # Show and save the plot
        plt.savefig(self.plotPath)
        plt.show()
