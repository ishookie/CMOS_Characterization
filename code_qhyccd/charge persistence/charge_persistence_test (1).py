import matplotlib.pyplot as plt 
import numpy as np 
import os 
import math 
import time
from astropy.io import fits
import re
import logging

import sys
sys.path.append("..")
import loadImage

sys.path.append("../cam")
from camera import DLAPICamera
from gateway import DLAPIGateway
from cam import camera, gateway

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class CHARGEPERSISTENCE: 

    def __init__(self, numBias=300, figureName='ChargePersistence_summed_test'):
        """
        Init for the charge persistence class. 

        Args:
            numBias (int, optional): Number of baises to take in 1s intervals. Defaults to 300.
            figureName (str, optional): _description_. Defaults to 'ChargePersistence_datalabel2'.
        """
        self.numBias = numBias
        self.rootPath = os.path.dirname(os.path.dirname(__file__))        
        self.outputDir = os.path.join(os.path.dirname(__file__), '..', 'plots', 'charge_persistence_plots')
        self.plotPath = os.path.join(self.outputDir, f'{figureName}_Plot.png')
    
    
    def takeLight(self, temp, expTime, number =1, readout_mode="High Gain"): 
        """
        Take a light frame. Saved in directory: data/chargePersistence/flat/{temp}/{readout mode}

        Args:
            temp (int): Temperature for frames to be saved at.
            expTime (int): Exposure time of light frame. 
            number (int, optional): Number of light images to be taken. Defaults to 1.
            readout_mode (str, optional): Readout mode of sensor. Either "High Gain" or "Low Gain" Defaults to "High Gain".
        """
        # Create necessary directories to save images to. 
        savedir = os.path.join(self.rootPath, 'data', 'chargePersistence', 'flat', f"{str(temp)}C")
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
        # Take frames
        for n in range(number): 
            result = cam.expose(imtype='light', readout_mode=readout_mode, exptime=float(expTime), filename=f"{temp}Cflat_{expTime}s_{readout_mode}-{n}.fits")
            # Check if exposure failed
            if "Error." in result.description:
                print(result.description)
                return
        logging.info("Long light exposure done. Close the shutter immediately.")
    

    def takeBias(self, temp, number =1, readout_mode="High Gain"): 
        """
        Take a bias image. 

        Args:
            temp (int): Temperature of sensor. 
            number (int, optional): Number of biases to take. Defaults to 1.
            readout_mode (str, optional): Options are either 'High Gain' or 'Low Gain'. Defaults to 'High Gain'.
        """
        # Create new directory for given temperature
        savedir = os.path.join(self.rootPath, 'data', 'chargePersistence', 'bias', str(temp))
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
        result = cam.expose(0, imtype='bias', readout_mode=readout_mode, filename=f"{temp}Cbias_{readout_mode}-{number}.fits")
        # Check if exposure failed
        if "Error." in result.description:
            print(result.description)
            return


    def takeImages(self, temp=5, expTime=3):
        """
        Take a light image immediately followed by a series of biases. 
        
        Args:
            temp (int, optional): Temperature of sensor. Defaults to 5.
            expTime (int, optional): Exposure time of light image. Defaults to 3.
        """
        # Take a light image at saturation 
        self.takeLight(temp=5, expTime=3)
        input("Press Enter after closing the shutter to start taking biases...") # Wait for user to close the shutter
        # Take biases 1 second inbetween 
        for i in range(self.numBias): 
            self.takeBias(temp=5, number=i)
            time.sleep(1) 
        
    
    def calcPersistence(self, temp=5):
        """
        Loads biases in order they are taken and calculates mean pixel values.

        Args:
            temp (int, optional): Temperature of sensor (what biases to load). Defaults to 5.
        """
        meanCounts = []
        dataPath = os.path.join(self.rootPath, 'data', 'chargePersistence', 'bias', f'{temp}', "High Gain")
        
        # Sort files before loading 
        filenames = sorted([filename for filename in os.listdir(dataPath) if filename.endswith(".fits")],
                           key=lambda x: int(re.search(r'(\d+).fits', x).group(1)))
        
        # Load bias images. Similar to loadImage.py but done here because order matters. 
        # Also mean is calculated immediately instead of returning a 2d array of each frame.
        # This is done because the pi runs out of memory if loading all images.
        for filename in filenames:
            filePath = os.path.join(dataPath, filename)
            try:
                with fits.open(filePath) as hdul:
                    data = hdul[0].data
                    meanCounts.append(np.sum(data))
            except Exception as e:
                print(f"Error reading {filePath}: {str(e)}")
 
        # fills a list up to numBias in 1 increments. Time list.
        times = [i for i in range(1, self.numBias+1)]    
        # Print first 5 values and times
        print(f"Mean Values: {meanCounts[:5]}")
        print(f"Times: {times[:5]}")
        # Plot values
        self.plotPersistence(meanCounts, times)
    
    
    def plotPersistence(self, meanVals, times):
        """
        Plot mean ADU vs time

        Args:
            meanVals (list): List of mean values
            times (list): List of times
        """
        plt.plot(times, meanVals, linestyle='-', label='Line Plot')
        plt.scatter(times, meanVals, color='red', marker='o', label='Data Points')
        
        plt.xlabel('Time (s)')
        plt.ylabel('Mean ADU')
        plt.title('Charge Persistence in Biases')
        plt.legend()  # Add legend to differentiate line plot and data points
        plt.savefig(self.plotPath)
        plt.show()  # Display the plot (optional)
        return
