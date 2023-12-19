import loadImage 
import numpy as np 
import math 
import os 
import sys
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from astropy.stats import sigma_clip
from astropy.io import fits
import time

sys.path.append("..")
import loadImage

sys.path.append("../cam")
from camera import DLAPICamera
from gateway import DLAPIGateway
from cam import camera, gateway

class DC: 
    def __init__(self, darkPath="", biasPath = '-5.0C_highGain', figureName='dark_current_plot_run3'):
        
        # Create dir path and load iamges
        self.rootPath = os.path.dirname(os.path.dirname(__file__)) 
        self.outputDir = os.path.join(os.path.dirname(__file__), '..', 'plots', 'dc_plots')
        self.plotPath = os.path.join(self.outputDir, f'{figureName}.png')

        
    def test(self, expTime, temp, readout_mode='High Gain'): 
        gateway = DLAPIGateway() 
        cam = DLAPICamera(gateway, model='stc', dirname=self.rootPath)
        cam.connect() 
        # Camera set point
        cam.set_temperature(temp)
        cam.start_cooling()
        print(self.rootPath)
        result = cam.expose(imtype='dark', readout_mode=readout_mode, exptime=float(expTime), filename=f"{temp}Cbias_{readout_mode}.fits")


    def createMasterBias(self, temp, readout_mode='High Gain'):
        """
        Given a temperature of pre existing bias images create a master bias from them. 
        Individual frames are sigma clipped and filled in with an average value before being stacked.

        Args:
            temp (int): Temperature of bias frames
            readout_mode (str): Readout mode of biases either "High Gain" or "Low Gain" 
        """
        if readout_mode == 'High Gain':
            gain = 'high_gain'
        else: 
            gain = 'low_gain'
        # Create save and frame directories 
        biasdir = os.path.join(self.rootPath, 'data', 'dc', 'bias', str(temp), readout_mode)
        savedir = os.path.join(self.rootPath, 'data', 'dc', 'master_bias', f"{temp}C_{gain}_master_bias.fits")
        # Load the biases
        fitsLoader = loadImage.fitsLoader(biasdir)
        bias = fitsLoader.loadImages() 
        # Apply clipping to each frame
        clippedMask = [] 
        for i in bias:
            maskedFrame = sigma_clip(i, sigma=3, maxiters=None)
            clippedMask.append(maskedFrame)
        
        # Stack the clipped biases
        stackedMask = np.ma.stack(clippedMask, axis=0)
        fillValue = np.ma.mean(stackedMask)
        stackedMask = np.median(stackedMask, axis=0)
        # Fill clipped values with the mean of other pixels (after stacking)
        stackedMask = stackedMask.filled(fillValue)
        stackedMask = stackedMask.astype(np.float32)
        fits.writeto(savedir, stackedMask)
        

    def takeBias(self, temp, number=20, readout_mode = 'High Gain'):
        """
        Take a bias image. 

        Args:
            temp (int): Temperature of sensor. 
            number (int, optional): Number of biases to take. Defaults to 20.
            readout_mode (str, optional): Options are either 'High Gain' or 'Low Gain'. Defaults to 'High Gain'.
        """
        # Create new directory for given temperature
        savedir = os.path.join(self.rootPath, 'data', 'dc', 'bias', str(temp))
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
        
        
    def takeDarks(self, temp, expTime, number = 10, readout_mode = "High Gain"): 
                # Create new directory for given temperature
        savedir = os.path.join(self.rootPath, 'data', 'dc', 'dark', f"{str(temp)}C", f"{str(expTime)}s")
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
        # Create camera objects
        gateway = DLAPIGateway() 
        print(f"Images saved to: {savedir}")
        cam = DLAPICamera(gateway, model='stc', dirname=savedir)
        cam.connect() 
        # Camera set point
        cam.set_temperature(temp)
        cam.start_cooling()
        # Take Biases
        for n in range(number): 
            result = cam.expose(imtype='dark', readout_mode=readout_mode, exptime=float(expTime), filename=f"{temp}Cdark_{readout_mode}-{n}.fits")
            # Check if exposure failed
            if "Error." in result.description:
                print(result.description)
                return
            
    def createTimeDict(self, temp, expTimes):
        """
        Create a dict where the key is the exposure time and the value is the 3D stack of frames

        Args:
            temp (int): Temperature in Celcius 
            expTimes (list): List of exposure times

        Returns:
            dict: Key is expTime value is total dark current. 
        """
        data = {}
        for time in expTimes: 
            dataPath = os.path.join(self.rootPath, 'data', 'dc', 'dark', f'{temp}C', f'{time}s', "High Gain")
            dataLoader = loadImage.fitsLoader(dataPath)
            ccdTemp = dataLoader.getHeaderInfo('CCD-TEMP')
            dataList = dataLoader.loadImages() 
            dataList = np.stack(dataList, axis=0)
            dataList = np.mean(dataList, axis=0) 
            data[time] = dataList 
        return data, ccdTemp

    
    def subtractMaster(self, data, master):
        
        for key, frame in data.items():
            print(f"Min: {np.min(frame)}")
            print(f"Max: {np.max(frame)}")
            print(f"Meam: {np.mean(frame)}")
            subFrames = frame - master
            subFrames = np.mean(subFrames)
            subFrames *= 1.2
            data[key] = subFrames
        return data
        
    
    def clipFrames(self, data): 
        
        for key, frameList in data.items():
            for i in range(len(frameList)):
                frame = frameList[i]
                maskedFrame = sigma_clip(frame, sigma=3, maxiters=None)
                fillValue = np.ma.mean(maskedFrame)
                maskedFrame.filled(fillValue)
                frameList[i] = maskedFrame 
                # print(f"after min: {np.min(maskedFrame)}")
                # print(f"after max: {np.max(maskedFrame)}")
                # print(f"after mean: {np.mean(maskedFrame)}")
        return data
            
    def fullFrameDC(self, expTimes = [1, 10, 60, 120, 240], temp1=None, temp2=None, temp3=None, temp4=None, temp5=None):
        """
        Test to calculate the dark current vs time for the entire image. 
        """
        
        if (temp1 or temp2 or temp3 or temp4 or temp5) is None:
            print("Must give 5 temperatures")
        
        
        data1, ccdTemp1 = self.createTimeDict(temp1, expTimes)
        data2, ccdTemp2 = self.createTimeDict(temp2, expTimes)
        data3, ccdTemp3 = self.createTimeDict(temp3, expTimes)
        data4, ccdTemp4 = self.createTimeDict(temp4, expTimes)
        data5, ccdTemp5 = self.createTimeDict(temp5, expTimes)
            
        # Load master 
        masterPath = os.path.join(self.rootPath, 'data', 'dc', 'master_bias')
        masterLoader = loadImage.fitsLoader(masterPath) 
        master = masterLoader.loadByFilename('high_gain_', 'temp')
        
        print(master.keys())

        # Get master frames
        master1 = master[str(temp1)]
        master2 = master[str(temp2)]
        master3 = master[str(temp3)]
        master4 = master[str(temp4)]
        master5 = master[str(temp5)]
        
        # Sigma clip individual dark frames
        # This is done because there are saturated "hot pixels"
        data1 = self.clipFrames(data1)
        data2 = self.clipFrames(data2)
        data3 = self.clipFrames(data3)
        data4 = self.clipFrames(data4)
        data5 = self.clipFrames(data5)
        
        # Subtract master from individual frames
        data1 = self.subtractMaster(data1, master1)
        data2 = self.subtractMaster(data2, master2)
        data2 = self.subtractMaster(data3, master3)
        data2 = self.subtractMaster(data4, master4)
        data2 = self.subtractMaster(data5, master5)
        
        print(f"{temp1}: {data1}")
        print(f"{temp2}: {data2}")
        print(f"{temp3}: {data3}")
        print(f"{temp4}: {data4}")
        print(f"{temp5}: {data5}")

        self.graphDCvsTIME(data1, data2, data3, data4, data5,ccdTemp1, ccdTemp2, ccdTemp3, ccdTemp4, ccdTemp5)
        return 
   

    def graphDCvsTIME(self, dict1, dict2, dict3, dict4, dict5,
                      temp1, temp2, temp3, temp4, temp5):
        """
        Plot Dark Current Count vs Time
        Also display Dark Current (slope of linear fit)
        """
        times = list(dict1.keys())
        values1 = list(dict1.values())
        values2 = list(dict2.values())
        values3 = list(dict3.values())
        values4 = list(dict4.values())
        values5 = list(dict5.values())

        # Plot the lines
        
        self.plot_line_with_slope(times, values1, label=f"{temp1}C")
        self.plot_line_with_slope(times, values2, label=f"{temp2}C")
        self.plot_line_with_slope(times, values3, label=f"{temp3}C")
        self.plot_line_with_slope(times, values4, label=f"{temp4}C")
        self.plot_line_with_slope(times, values5, label=f"{temp5}C")

        # Customize the plot
        plt.xlabel('Time')
        plt.ylabel('Dark Current')
        plt.title('Dark Current Over Time')
        plt.legend()  # Add legend to distinguish lines
        plt.grid(True) # griddy 
        plt.savefig(self.plotPath)
        # Show the plot
    
        plt.show()

    def plot_line_with_slope(self, times, values, label):
        # Calculate the rise-over-run (slope)
        rise = values[-1] - values[0]
        run = times[-1] - times[0]
        slope = rise / run
        

        # Plot the line
        plt.plot(times, values, label=f'{label} (DC: {slope:.4f})')
