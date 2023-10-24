import sys
sys.path.append("..")
import loadImage
import os 
import numpy as np

sys.path.append("..")

def averageWavelength(data):
    """
    Takes a dictionary, key values are wavelength and then averages
    each frame into one value. Then returns a dict with key wavelength 
    and data that averaged value 
    """
    averagedData = {}
    for wavelength, image in data.items():
            if image:
                # Calculate the mean of all image arrays for the current wavelength
                averagedValue = np.mean(image)
                averagedData[wavelength] = averagedValue

    return averagedData

if __name__ == '__main__':
    absPath = os.path.dirname(__file__)
    
    fullPath = os.path.join(absPath, 'exposures')
    fitsLoader = loadImage.fitsLoader(fullPath) 
    fitsLoader.loadByFilename() 
    
    averagedData = averageWavelength(fitsLoader.keyImages)
    print(averagedData)

    for wavelength, image in fitsLoader.keyImages.items():
        # Get the number of data bits in the image using the dtype attribute
        print(f'Wavelength: {wavelength}, Data Bits: {len(image) }')