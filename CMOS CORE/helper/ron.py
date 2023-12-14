import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from astropy.stats import sigma_clip
from astropy.io import fits
from scipy.ndimage import uniform_filter

sys.path.append("..")
import loadImage

sys.path.append("../cam")
from camera import DLAPICamera
from gateway import DLAPIGateway
from cam import camera, gateway


class RON:
    # Sigma Threshold for sigma clipping 
    threshold = 10

    
    def __init__(self, relativePath=None, figureName=None):
        # Create dir path and load images
        # Move up two levels to the root directory
        self.rootPath = os.path.dirname(os.path.dirname(__file__)) 
        if relativePath:
            self.figureName = figureName
            self.rootPath = os.path.dirname(os.path.dirname(__file__)) 
            self.fullPath = os.path.join(self.rootPath, 'data', relativePath)
            # self.fullPath = os.path.join(self.absPath, relativePath)
            self.fitsLoader = loadImage.fitsLoader(self.fullPath)
            self.fitsLoader.loadImages()
        
        # Output path for figures
        if figureName:
            self.outputDir = os.path.join(os.path.dirname(__file__), '..', 'plots', 'ron_plots')
            self.plotPath = os.path.join(self.outputDir, f'{figureName}.png')
        else: 
            self.plotPath = os.path.join(os.path.dirname(__file__), '..', 'plots', 'ron_plots')
            


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
        biasdir = os.path.join(self.rootPath, 'data', 'ron', str(temp), readout_mode)
        savedir = os.path.join(self.rootPath, 'data', 'ron', 'master_bias', f"{temp}C_{gain}_master_bias.fits")
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
        print(type(stackedMask))
        print(f"shape: {np.shape(stackedMask)}")
        print(f"min: {np.min(stackedMask)} max: {np.max(stackedMask)}")
        fits.writeto(savedir, stackedMask)
    
    
    def takeData(self, temp, number=10, readout_mode="High Gain"):
        """
        Take Bias images. 

        Args:
            temp (int): Temperature of sensor to take data at. 
            number (int, optional): Number of bias frames to take. Defaults to 10.
            readout_mode (str, optional): Readout mode of sensor either: "High Gain" or "Low Gain". Defaults to "High Gain".
        """
        # Create new directory for given temperature
        savedir = os.path.join(self.rootPath, 'data', 'ron', str(temp))
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

    
    def calcRON(self, dataPath, plotName, binning=1):
        """
        Calculates RON by subtracting the master from individual biases.
        Then calcualtes the pixel wise std of all frames and divides by sqrt 2.

        Args:
            dataPath (str:): Path to bias images something of the form: -5/High Gain
            plotName (str:): Name for the heatmap and histogram plot
            binning (int, optional): Square bin size for making the heatmap. Defaults to 1 (no binning).
        """
        # Load master bias
        masterPath = os.path.join(self.rootPath,'data', 'ron', 'master_bias')
        masterLoader = loadImage.fitsLoader(masterPath)
        masterBias = masterLoader.loadImages() 
        
        # Load bias images
        biasPath = os.path.join(self.rootPath, 'data', 'ron', dataPath)
        biasLoader = loadImage.fitsLoader(biasPath)
        biasFrames = biasLoader.loadImages()
        
        # Calculate STD
        stack = np.stack(biasFrames, axis=0)
        finish = stack - masterBias
        finish = np.std(finish, axis=0)
        finish /= np.sqrt(2) 
        
        self.plotStatistics(finish, plotName, binning) 


    def plotStatistics(self, data, plotName, binning):
        """
        Prints: Min, Max and Mean values.
        Creates a histogram of RMS pixel values vs log(count)
        Creates a heatmap of RON absolute values. 

        Args:
            data (np array): Array of pixel values representing the readout noise 
            plotName (str): Name to prefix plot file names with.
            binning (int): square binning size for heatmap. Defaults to 1
        """                        
        # Print various statistics 
        print(f"Min Value: {np.min(data)}")
        print(f"Max Value: {np.max(data)}")
        print(f"Mean Value: {np.mean(data)}")
        
        # Create Histogram
        stdArray_flat = data.flatten()
        plt.hist(stdArray_flat, bins=100)
        plt.title('RON Histogram')
        plt.xlabel('RON Values (ADU)')
        plt.ylabel('log(count)')
        plt.yscale('log')
        plt.savefig(os.path.join(self.plotPath, f"{plotName}_histogram.png"))
        
        # Create a heatmap 
        data = uniform_filter(data, size=binning, mode='constant')[::binning, ::binning]
        plt.figure()  # Create a new figure for the heatmap
        heatmap = plt.imshow(data, cmap='magma', interpolation='nearest')
        plt.colorbar(heatmap)
        plt.savefig(os.path.join(self.plotPath, f"{plotName}_heatmap.png"))
        plt.show()
    

    def sampleSize(self, zScore=1.96, MOE=0.02):
        """"
        Calculate the required sample size (n) for a given confidence interval
        and margin of error (MOE) default values:
        CI = 1.96 (95%)
        MOE = 2% 
        """
        self.calcRON()
        std = np.mean(np.sqrt(self.clipped))
        MOE *= np.mean(self.clipped)
        n = (zScore**2 * std**2) / MOE**2 
        print(n) 


    def marginOfError(self, zScore=1.96, n=545):
        """
        Helper function to calculate the margin of error for a given number of biases. 
        """
        self.calcRON()
        std = np.mean(np.sqrt(self.clipped))
        MOE = np.sqrt((zScore**2 * std**2) / n)
        MOE /= np.mean(self.clipped) 
        print(MOE) 