import matplotlib.pyplot as plt 
import numpy as np 
import os 
import logging
import sys
sys.path.append("..")
import loadImage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class LINEARITY: 

    def __init__(self, roiSize=500, figureName='LinearityTest_2min'):
        """
        Init for Linearity class. 

        Args:
            roiSize (int, optional): nxn pixel box for linearity calculations. Defaults to 500.
            figureName (str, optional): Name of saved plot. Defaults to 'LinearityTest_2min'.
        """
        self.roiSize = roiSize
        self.rootPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.outputDir = os.path.join(self.rootPath, 'plots', 'linearity_plots')
        self.plotPath = os.path.join(self.outputDir, f'{figureName}_Plot.png')

        logging.info(f"Root path set to: {self.rootPath}")
        logging.info(f"Output directory set to: {self.outputDir}")

        # Ensure the output directory exists
        if not os.path.exists(self.outputDir):
            os.makedirs(self.outputDir)
            logging.info(f"Created output directory: {self.outputDir}")

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
        logging.info(f"Loading flat frames from {flatPath}")
        flatLoader = loadImage.fitsLoader(flatPath)
        flats = flatLoader.sortImages('EXPTIME') 
        
        # Calculate mean values 
        expTimeVals = []
        meanVals = []
        for t, frame in flats.items():
            expTimeVals.append(t)
            meanVal = np.mean(frame)
            meanVals.append(meanVal)
        
        logging.info(f"Mean ADU values: {meanVals}")
        logging.info(f"Exposure times: {expTimeVals}")
        self.plotCurve(expTimeVals, meanVals) 
        

    def plotCurve(self, expTimeVals, meanVals):
        """
        Plot linearity curve and save figure to:
        plots/linearity

        Args:
            expTimeVals (list): List of exposure time values. 
            meanVals (list): List of mean values of frames.
        """
        # Filter data to exclude values over 4000 from the linear fit
        filtered_data = [(t, m) for t, m in zip(expTimeVals, meanVals) if m <= 4050]
        x_data_fit, y_data_fit = zip(*filtered_data)
        # Convert lists to numpy arrays for linear regression
        x_data_fit = np.array(x_data_fit)
        y_data_fit = np.array(y_data_fit)
        # Get linear fit
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
        logging.info(f"Plot saved to: {self.plotPath}")
        plt.show()

if __name__ == "__main__":
    # Create an instance of the LINEARITY class
    lin_test = LINEARITY()

    # Specify the temperature and readout mode
    temperature = -5
    readout_mode = 'High Gain'

    # Calculate and plot the linearity curve
    lin_test.calcCurve(temp=temperature, readout_mode=readout_mode)
