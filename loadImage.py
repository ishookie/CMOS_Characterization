import os
import numpy as np 
from astropy.io import fits
from collections import defaultdict 


class fitsLoader:

    def __init__(self, folderPath):
        self.folderPath = folderPath
        self.images = []
        self.keyImages = {}

    """
    Takes fits images from a folder whos path is specified in
    the constructor and adds the image data (primary header)
    to a list called "images"
    """
    def loadImages(self):
        for filename in os.listdir(self.folderPath):
            # incase there is a non-fit file in the folder
            if filename.endswith(".fit"):
                filePath = os.path.join(self.folderPath, filename)
                try:
                    with fits.open(filePath) as hdul:
                        data = hdul[0].data
                        self.images.append(data)
                except Exception as e:
                    print(f"Error reading {filePath}: {str(e)}")
    
    def getHeaderInfo(self, str):
        """
        Gets exposure time from a fits header of the first file in a given directory 
        """
        all_files = os.listdir(self.folderPath)
        fits_files = [file for file in all_files if file.endswith('.fit')]

        if not fits_files:
            print("No fits files in directory")
        else:
            fitsFile = fits.open(os.path.join(self.folderPath, fits_files[0]))
            header = fitsFile[0].header
            result = header.get(str)
            if not result: 
                print(f"Argument {str} not found in fits header")
            return result
        

    def sortImages(self, str):
        """
        Similar to loadImages but stores image data in a dictionary 
        where the key is the given str argument
        used in dc with exposure time as the key
        """
        for filename in os.listdir(self.folderPath):
            if filename.endswith(".fit"):
                filePath = os.path.join(self.folderPath, filename)
                try:
                    with fits.open(filePath) as hdul:
                        key = hdul.get(str) 
                        if key not in self.keyImages:
                            self.keyImages[key] = []
                            
                        self.keyImages[key].append(hdul[0].data)
                               
                except Exception as e:
                    print(f"Error reading {filePath}: {str(e)}")

