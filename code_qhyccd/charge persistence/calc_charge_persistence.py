import matplotlib.pyplot as plt 
import numpy as np 
import os 
import re
import logging
from astropy.io import fits

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class CHARGEPERSISTENCE: 

    def __init__(self, numBias=300, figureName='ChargePersistence_summed_test'):
        """
        Init for the charge persistence class. 

        Args:
            numBias (int, optional): Number of biases to take in 1s intervals. Defaults to 300.
            figureName (str, optional): _description_. Defaults to 'ChargePersistence_datalabel2'.
        """
        self.numBias = numBias
        self.rootPath = os.path.dirname(os.path.dirname(__file__))        
        self.outputDir = os.path.join(self.rootPath, 'plots', 'charge_persistence_plots')
        self.plotPath = os.path.join(self.outputDir, f'{figureName}_Plot.png')
        if not os.path.exists(self.outputDir):
            os.makedirs(self.outputDir)
    
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
                    meanCounts.append(np.mean(data))
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
    
def main():
    charge_persistence = CHARGEPERSISTENCE()
    charge_persistence.calcPersistence()

if __name__ == "__main__":
    main()
