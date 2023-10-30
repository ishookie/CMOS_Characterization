import sys
sys.path.append("..")
import loadImage
import os 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.constants import h, c, e

#**********************************************************************************
    # THIS FILE IS ABSOLUTLY GROSS AND DISGUSTING AND NEEDS A SERIOUS OVERHAUL 
    # IT IS NOT WELL ORGANIZED AND I NEED TO SIT DOWN AND PLAN IT OUT.
    
    # ALSO THE QE I CALCULATED IS LIKE 1E-40 WHICH IS SUPER WRONG (lol)
#**********************************************************************************

def readCSV(filepath='data/photodiode/example.csv'):
    df = pd.read_csv(filepath)

    # Group the DataFrame by 'Wavelength' and calculate the mean of 'Readings' for each group
    df = df.groupby('Wavelength')['Readings'].mean().reset_index()

    
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
        sImg = image - darkFrames['12']
        scienceImages[wavelength] = sImg
        
    return scienceImages
        

def calcSignal(scienceImages: dict):
    """
    Calc signal value by taking median then multiplying by eGain.
    (hard coded eGain here, cringe and BAD)
    Args:
        scienceImages (dict): Images with key as wavelength.

    Returns:
        scienceMedian (dict): Median values, key is wavelength.  
    """
    scienceMedian = {} 
    for wavelength, image in scienceImages.items():
        med = np.median(image) * 5.419037
        scienceMedian[wavelength] = med
    return scienceMedian

def divByTime(data):
    result = {}
    for wavelength, image in data.items():
        res = image/12
        result[int(wavelength)] = res
    return result 
        

def dropMissingData(data):
    """_summary_

    Args:
        data (df): Dataframe containing unclean data

    Returns:
        data (df): Data frame with dropped missing values
    """
    data.dropna(subset=['Wavelength', 'Readings'], inplace=True)
    return data
    

if __name__ == '__main__':
    
    # Constant for photodiode
    hcq = h*c*e
    
    absPath = os.path.dirname(__file__)
    
    # Load light frames (12s exp)
    fullPathLight = os.path.join(absPath, 'data/exposures/time3')
    lightFrames = loadImage.fitsLoader(fullPathLight) 
    lightFrames.loadByFilename("nm") 
    # Load dark frames
    fullPathDark = os.path.join(absPath, 'data/darks')
    darkFrames = loadImage.fitsLoader(fullPathDark)
    darkFrames.loadByFilename("s_")
    
    # Stack Frames
    stackedDark = stackByKey(darkFrames.keyImages)
    stackedLight = stackByKey(lightFrames.keyImages)
    
    # Subtract dark frames from light
    scienceImages = subFrames(stackedLight, stackedDark)
    
    # Take median and multiply by eGain 
    scienceMedian = calcSignal(scienceImages) 
    
    sensorTerm = divByTime(scienceMedian)
    
 # ---------------------PhotoDiode-------------------------------------------------
 
    # Open csv files (hard coded path turned into variable)
    photoDiodeLight = pd.read_csv('data/photodiode/example.csv')
    photoDiodeDark = pd.read_csv('data/photodiode/photoDiodeDark.csv')

    # Drop any missing values from photodiode readings
    photoDiodeLight = dropMissingData(photoDiodeLight)
    photoDiodeDark = dropMissingData(photoDiodeDark)
    
    # Round wavelength values to nearest integer so data can be grouped
    photoDiodeLight['Wavelength'] = photoDiodeLight['Wavelength'].round(1)
    photoDiodeDark['Wavelength'] = photoDiodeDark['Wavelength'].round(1)

    # Group the data by wavelength and calculate the average reading for each wavelength
    photoDiodeLight = photoDiodeLight.groupby('Wavelength')['Readings'].mean().reset_index()
    photoDiodeDark = photoDiodeDark.groupby('Wavelength')['Readings'].mean().reset_index()

    # Merge the two DataFrames on the 'wavelength' column to align the dark readings with the example readings
    photoDiodeScience = pd.merge(photoDiodeLight, photoDiodeDark, on='Wavelength', suffixes=('_Light', '_Dark'))

    # Subtract the dark readings from the example readings to get the corrected values
    photoDiodeScience['science_reading'] = photoDiodeScience['Readings_Light'] - photoDiodeScience['Readings_Dark']
    
    # 2 nA - photodiode current at R1
    photoDiodeScience['science_reading'] = photoDiodeScience['science_reading']
    
    photodiodeTerm = {} 
    for index, row in photoDiodeScience.iterrows():
        wavelength = row['Wavelength']
        science_reading = row['science_reading']
        result = (wavelength * science_reading) / hcq
        photodiodeTerm[wavelength] = result

#-------------------------Calc QE------------------------------------------------------------------------------
    results = {}

    print(photodiodeTerm) 
    print()
    print(sensorTerm)
    # Divide values at each wavelength and store the result
    for wavelength in photodiodeTerm:
        if wavelength in sensorTerm:
            result = sensorTerm[wavelength] / photodiodeTerm[wavelength]
            results[wavelength] = result

    print(results) 
    # Convert the results dictionary into lists for plotting
    wavelengths = list(results.keys())
    division_results = list(results.values())

    # Create a plot
    plt.figure()
    plt.plot(wavelengths, division_results, marker='o', linestyle='-')
    plt.title("SensorTerm / PhotodiodeTerm vs. Wavelength")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("SensorTerm / PhotodiodeTerm")
    plt.grid(True)

    # Show the plot
    plt.savefig("plot.png")
