import loadImage 
import numpy as np 
import math 
import os 
import sys
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

sys.path.append("..")
import loadImage

sys.path.append("../cam")
from camera import DLAPICamera
from gateway import DLAPIGateway
from cam import camera, gateway


class DC: 
    def __init__(self, darkPath="", biasPath = '-5.0C_highGain'):
        
        # Create dir path and load iamges
        self.rootPath = os.path.dirname(os.path.dirname(__file__)) 
        # self.fullPath = os.path.join(self.absPath, '..', 'frames', darkPath)
        # self.fitsLoader = loadImage.fitsLoader(self.fullPath)
        # # Load images with exposure time as key -> keyImages
        # self.fitsLoader.sortImages('EXPTIME')
        # self.diffDict = {} 
        # self.darkCurrents = {}
        # self.diff = [] 
        # # Load bias to create master bias 
        # self.fullPathBias = os.path.join(self.absPath, '..', 'frames', biasPath)
        # self.fitsLoaderBias = loadImage.fitsLoader(self.fullPathBias)
        # self.fitsLoaderBias.loadImages()


    def takeBias(self, temp, readout_mode = 'High Gain'):
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
            result = cam.expose(imtype='dark', readout_mode=readout_mode, exptime=float(expTime), filename=f"{temp}Cbias_{readout_mode}-{n}.fits")
            # Check if exposure failed
            if "Error." in result.description:
                print(result.description)
                return
            
            
    def fullFrameDC(self, temp1, temp2):
        """
        Test to calculate the dark current vs time for the entire image. 
        """
        # Load Master
        # 
        # 
        # 
        # 
        # 
        # 
        # 
        # Create master bais 
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
        return 
   

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
