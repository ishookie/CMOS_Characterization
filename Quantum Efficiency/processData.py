import sys
sys.path.append("..")
import loadImage
import os 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.constants import h, c, e


#**********************************************************************************
# *** NEW PLAN ***
#
# For a given exp time. 
# 1: Calculate Sensor Term
#   1.1 Load light frames: {wavelength: frame1, frame2...}
#   1.2 Load dark frames: {expTime: frame1, frame2...}
#   1.3 Stack (average) light frames at each wavelength: {wavelength1: stackFrame wavelength2: stackFrame}
#   1.4 Stack (average) dark frames for the given exp time. {expTime: stackFrame}
#   1.5 Light frame - dark frame at each wavelength {wavelength1: scienceFrames wavelength2: scienceFrames}
#   1.6 Sum all pixels in science frames at each wavelength {wavelength1: scienceSum wavelength2: scienceSum}
#   1.7 Multiply summed pixels by gain {wavelength1: e- wavelength2: e-}
#   1.8 Divide summed pixels by exposure time {wavelength1: e-/t, wavelength2: e-/t}
#   1.9 Round wavelength to nearest integer (compatability with photodiode dict)
#
# 2: Calculate Photodiode Term 
#   2.1 Load light data: [df: wl, reading]
#   2.2 Load dark data: [df: wl, reading] (constant wl doesnt matter here)
#   3.3 Clean data - drop any missing values
#   3.4 Round wavelength to nearest integer (compatability)
#   3.5 Group and average readings by wavelength 
#   3.6 Merge dataframes: [df: wl, lightReading, darkReading]
#   3.7 Light data -dark data = science data
#   3.8 Calculate photodiode term at each wl: (science_reading * wl) / (h * c)
#   3.9 Put photodiode term at each wl into dict: {wavelength1: #p wavelength2: #p}
#
# 3: Calculate QE
#   3.1 At each wavelength: QE = sensor_term / photodiode_term
#   3.2 Graph it
#
#**********************************************************************************



def loadFrames(exposurePath='data/exposures/time1', darkPath = 'data/darks'): 
    
    absPath = os.path.dirname(__file__)
    # Load light frames (12s exp)
    fullPathLight = os.path.join(absPath, exposurePath)
    lightFrames = loadImage.fitsLoader(fullPathLight) 
    lightFrames.loadByFilename("nm") 
    # Load dark frames
    fullPathDark = os.path.join(absPath, darkPath)
    darkFrames = loadImage.fitsLoader(fullPathDark)
    darkFrames.loadByFilename("s_")
    return lightFrames.keyImages, darkFrames.keyImages

    
def graphPhotodiode(filepath='data/photodiode/example.csv'):
    """
    Graph wavelength vs signal of the photodiode. Successive readings
    at a given wavelength are averaged. 

    Args:
        filepath (str, optional): Path to VSC file. 
        Defaults to 'data/photodiode/example.csv'.
    """
    df = pd.read_csv(filepath)
    # Group the DataFrame by 'Wavelength' and calculate the mean of 'Readings' for each group
    df = df.groupby('Wavelength')['Readings'].mean().reset_index()
    # Plot data
    plt.figure()
    plt.plot(df['Wavelength'], df['Readings'], marker='o')
    plt.xlabel('Wavelength')
    plt.ylabel('Readings')
    plt.title('Readings vs. Wavelength')
    plt.grid(True)
    plt.show()
    

def stackByKey(data):
    """
    Takes a dictionary, key values are wavelength and then averages
    all the frames into one pixel wise. Then returns a dict with key 
    wavelength and data that averaged value.

    Args:
        data (dict): Frames to be averaged. 

    Returns:
        averagedData (dict): Averaged frames.  
    """
    averagedData = {}
    for wavelength, image in data.items():
            if image:
                # Calculate the mean of all image arrays for the current wavelength
                averagedValue = np.mean(image, axis=0)
                averagedData[wavelength] = averagedValue
    return averagedData

def subFrames(lightFrames: dict, darkFrames: dict):
    """
    Subtract dark images from light. Right now the exp time
    is hard coded which is not great. 

    Args:
        lightFrames (dict): Light Frames, key is wavelength. 
        darkFrames (dict): Dark frames, key is exp time. 
    """
    scienceImages = {} 
    for wavelength, image in lightFrames.items():
        
        sImg = image - darkFrames['7']
        # Set any negative values to 0
        sImg[sImg < 0] = 0
        scienceImages[wavelength] = sImg
        
        min_value = np.min(sImg)
        max_value = np.max(sImg)
        average_value = np.mean(sImg)
        
        # plt.imshow(sImg, cmap='viridis')  # 'viridis' is a colormap for brighter colors
        # plt.colorbar()  # Add a colorbar for reference
        # plt.title("Heatmap of 2D Array")
        # plt.savefig(f'test_{wavelength}nm.png')
        # plt.clf()

        # print(f"Minimum value: {min_value}")
        # print(f"Maximum value: {max_value}")
        # print(f"Average value: {average_value}")
    return scienceImages
        

def calcSensorTerm(scienceImages: dict, eGain = 5.419037, expTime=7):
    """
    Calc signal value by taking summing all pixels 
    then multiplying by eGain.
    (hard coded eGain here, cringe and BAD)
    Args:
        scienceImages (dict): Images with key as wavelength.

    Returns:
        scienceMedian (dict): Median values, key is wavelength.  
    """
    sensorTerm = {} 
    for wavelength, image in scienceImages.items():
        sum = np.sum(image) * eGain # sum the data
        sum = sum / expTime # divide by exposure time
        # Round wavelength to integer
        sensorTerm[int(wavelength)] = sum
    print(f"Sensor Term: {sensorTerm}")
    return sensorTerm

def loadAndCleanCsv(filepath):
    """
    Loads a csv file into a dataframe, drops missing values and
    rounds wavelength values to nearest integer. 

    Args:
        filepath (str): Relative path to csv file

    Raises:
        ValueError: When no filepath is provided

    Returns:
        data (df): loaded and cleaned data 
    """
    if not filepath: 
        raise ValueError("Please provide a csv filepath.")
    
    data = pd.read_csv(filepath)
    # Drop missing values in place
    data.dropna(subset=['Wavelength', 'Readings'], inplace=True)
    # Round wavelength to integer
    data['Wavelength'] = data['Wavelength'].round(1)
    return data

def subPhotodiode(lightData, darkData):
    # Average data over a wavelength value
    lightData = lightData.groupby('Wavelength')['Readings'].mean().reset_index()
    darkData = darkData.groupby('Wavelength')['Readings'].mean().reset_index()
    # Merge and allign dataframes
    merged = pd.merge(lightData, darkData, on='Wavelength', suffixes=('_Light', '_Dark'))
    # Subtract darks from light
    merged['science_reading'] = merged['Readings_Light'] #- merged['Readings_Dark']
    return merged

def calcPhotodiodeTerm(data):
    photodiodeTerm = {} 
    for index, row in photoDiodeScience.iterrows():
        wavelength = row['Wavelength']
        science_reading = row['science_reading']
        # Calc Term 
        result = (wavelength * 1e-9 * science_reading) / (h*c)
        photodiodeTerm[wavelength] = result
    return photodiodeTerm

def calcQE(sensorTerm, photodiodeTerm, printData=True, plot=True):
    results = {}
    # Divide values at each wavelength and store the result
    for wavelength in photodiodeTerm:
        if wavelength in sensorTerm:
            result = (sensorTerm[wavelength] / photodiodeTerm[wavelength]) * 100
            results[wavelength] = result

    if printData: 
        print(f"Photodiode Term: {photodiodeTerm}")
        print(f"Sensor Term: {sensorTerm}")
        print(results)
        
    if plot: 
        # Format data for plot
        wavelengths = list(results.keys())
        division_results = list(results.values())
        # Create a plot
        plt.figure()
        plt.plot(wavelengths, division_results, marker='o', linestyle='-')
        plt.title("Quantum Efficiency")
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("QE (%)")
        plt.grid(True)
        # Save Plot
        plt.savefig("QE.png")
        
    return results

    
    
if __name__ == '__main__':
 # ---------------------Sensor----------------------------------------------------    
    # Load Frames
    lightFrames, darkFrames = loadFrames()
    # Stack Light/dark frames 
    stackedLight = stackByKey(lightFrames)
    stackedDark = stackByKey(darkFrames) 
    # Subtract dark from light frames     
    scienceFrames = subFrames(stackedLight, stackedDark)
    # Calculate term
    sensorTerm = calcSensorTerm(scienceFrames)

 # ---------------------PhotoDiode-------------------------------------------------
 
    # Load and clean csv data
    photoDiodeLight = loadAndCleanCsv('data/photodiode/example.csv')
    photoDiodeDark = loadAndCleanCsv('data/photodiode/photoDiodeDark.csv')
    # Subtract dc 
    photoDiodeScience = subPhotodiode(photoDiodeLight, photoDiodeDark)
    # Calculate term
    photodiodeTerm = calcPhotodiodeTerm(photoDiodeScience)

#-------------------------Calc QE----------------------------------------------------
    # Calc, printing terms/result and plotting on by default
    QE = calcQE(sensorTerm, photodiodeTerm)
    

