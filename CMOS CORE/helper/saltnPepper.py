import matplotlib.pyplot as plt 
import numpy as np 
import os 
import math 
import time
from astropy.io import fits
import re

import sys
sys.path.append("..")
import loadImage

sys.path.append("../cam")
from camera import DLAPICamera
from gateway import DLAPIGateway
from cam import camera, gateway

class SALTNPEPPER: 

    def __init__(self, figureName='S&P_12std_scaled_red'):
        """
        Init for the salt and pepper class. 

        Args:
            numBias (int, optional): Number of baises to take in 1s intervals. Defaults to 300.
            figureName (str, optional): _description_. Defaults to 'ChargePersistence_datalabel2'.
        """
        self.roiSize = 50
        self.stdVar = 12
        self.rootPath = os.path.dirname(os.path.dirname(__file__))        
        self.outputDir = os.path.join(os.path.dirname(__file__), '..', 'plots', 'saltnPepper_plots')
        self.plotPath = os.path.join(self.outputDir, f'{figureName}_Plot.png')
    
    
    def takeBias(self, temp, number =10, readout_mode="High Gain"): 
        """
        Take a bias images. 

        Args:
            temp (int): Temperature of sensor. 
            number (int, optional): Number of biases to take. Defaults to 1.
            readout_mode (str, optional): Options are either 'High Gain' or 'Low Gain'. Defaults to 'High Gain'.
        """
        # Create new directory for given temperature
        savedir = os.path.join(self.rootPath, 'data', 'saltnPepper', 'bias', str(temp))
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
            result = cam.expose(0, imtype='bias', readout_mode=readout_mode, filename=f"{temp}Cbias_{readout_mode}-{n}.fits")
        # Check if exposure failed
            if "Error." in result.description:
                print(result.description)
                return
    
    
    def calcSaltnPepper(self, temp=-5, readout_mode='High Gain'): 
        """
        Take N biases identify a small ROI then plot ADU of pixels.
        graph all pixels change colour for ones +/- 3x RON. 
        """
        # Load bias images
        biasPath = os.path.join(self.rootPath, 'data', 'saltnPepper', 'bias', f"{str(temp)}", readout_mode)
        biasLoader = loadImage.fitsLoader(biasPath)
        biasFrames = biasLoader.loadImages()
        

        # Get std and mean of first frame
        # Used to find pixels of interest
        std = np.std(biasFrames[0])
        mean = np.mean(biasFrames[0])
        
        # Get coordinates of pixels 
        highStd = np.where(biasFrames[0] > (mean + self.stdVar*std))
        
        print(f"Starting x ROI: {highStd[0][0]}, Starting y ROI: {highStd[1][0]}")

        self.midROI(highStd)
        
        # Initialize lists to store pixel values and corresponding frame numbers
        pixel_values = []
        frame_numbers = []

        # Iterate through the subset of frames
        for i, frame in enumerate(biasFrames):
            # Get the ROI
            subset = frame[self.startX:self.endX, self.startY:self.endY]
            # List of frame numbers
            frame_numbers.append(i) 
            # List of lists containing pixel Values
            flat_array  = subset.flatten()
            pixel_values.append(list(flat_array))
        

        # Chart all pixels across frames
        # Not sure how to change colours of outliers
        # without tanking performance. 
        for x, y in zip(frame_numbers, pixel_values):            
            plt.scatter([x]*len(y), y,  color='red')



        plt.ylim(210, 250)
        plt.xlabel('Frame Number')
        plt.ylabel('ADU Pixel Value')
        plt.title("Salt and Pepper Noise (Random Telegraph Noise) +/-12 std")
        # plt.legend()

        plt.savefig(os.path.join(self.plotPath))
        # Show the plot
        plt.show()

   
    def midROI(self, indexes): 
        """
        Given coordinates of a high variance pixel get the ROI region 

        Args:
            indexes (tuple[list]): A tuple of lists containing the x and y coordinates of
            high variance pixels. 
        """
        self.startX = indexes[0][0]
        self.startY = indexes[1][0]
        self.endX = self.startX + self.roiSize 
        self.endY = self.startY + self.roiSize