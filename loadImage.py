import os
import numpy as np 
from astropy.io import fits
from collections import OrderedDict
import re


class fitsLoader:

    def __init__(self, folderPath):
        self.folderPath = folderPath
        self.images = []
        self.keyImages = {}


    def loadImages(self):
        """
        Takes fits images from a folder whos path is specified in
        the constructor and adds the image data (primary header)
        to a list called "images"
        """
        for filename in os.listdir(self.folderPath):
            # incase there is a non-fit file in the folder
            if filename.endswith(".fits"):
                filePath = os.path.join(self.folderPath, filename)
                try:
                    with fits.open(filePath) as hdul:
                        data = hdul[0].data
                        self.images.append(data)
                except Exception as e:
                    print(f"Error reading {filePath}: {str(e)}")
        return self.images
    
    def getHeaderInfo(self, str):
        """
        Gets data from a given header string. For example EXPTIME to get 
        exposure time. 

        Args:
            str (str): Fits header to load data from. 

        Returns:
            _type_: data associated with header. 
        """
        all_files = os.listdir(self.folderPath)
        fits_files = [file for file in all_files if file.endswith('.fits')]

        if not fits_files:
            print("No fits files in directory")
        else:
            fitsFile = fits.open(os.path.join(self.folderPath, fits_files[0]))
            header = fitsFile[0].header
            result = header.get(str)
            if not result: 
                print(f"Argument {str} not found in fits header for image: {self.folderPath}\n for image: {fits_files[0]}")
            return result
        

    def sortImages(self, head):
        """
        Similar to loadImages but stores image data in a ordered dictionary 
        where the key is the given header string argument.
        Used in dc with exposure time as the key.

        Args:
            head (str): Header value to sort images by.
        """
        for filename in os.listdir(self.folderPath):
            if filename.endswith(".fits"):
                filePath = os.path.join(self.folderPath, filename)
                try:
                    with fits.open(filePath) as hdul:
                        header = hdul[0].header
                        key = header.get(head)
                        data = hdul[0].data

                        if key not in self.keyImages:
                            self.keyImages[key] = []

                        self.keyImages[key].append(data)
                except Exception as e:
                    print(f"Error reading {filePath}: {str(e)}")

        self.keyImages = OrderedDict(sorted(self.keyImages.items()))
        return self.keyImages

    def loadByFilename(self, delimiter: str, extraction_type: str):
        """
        Load fits images by filename. Delimiter is where the string is split.
        Extraction type can be either 'wavelength' or 'exposure_time'.
        Used for loading images taken in QE testing.

        Args:
            delimiter (str): delimiter to parse filename.
            extraction_type (str): type of information to extract ('wavelength' or 'exposure_time').

        Returns:
            self.keyImages (dict): Sorted dictionary of numpy arrays
            containing pixel information.
        """
        for filename in os.listdir(self.folderPath):
            # in case there is a non-fit file in the folder
            if filename.endswith(".fits"):
                # Extract information from filename using regular expression
                if extraction_type == 'wavelength':
                    pattern = rf'\d+s_{delimiter}(\d+)nm'
                elif extraction_type == 'exposure_time':
                    pattern = rf'(\d+)s_{delimiter}\d+nm'
                elif extraction_type == 'temp':
                    pattern = rf'(-?\d+)C_{delimiter}'

                match = re.search(pattern, filename)
                if match:
                    info = match.group(1)
                    filePath = os.path.join(self.folderPath, filename)
                    try:
                        with fits.open(filePath) as hdul:
                            data = hdul[0].data
                            self.images.append(data)
                            if info not in self.keyImages:
                                self.keyImages[info] = []
                            self.keyImages[info].append(data)
                    except Exception as e:
                        print(f"Error reading {filePath}: {str(e)}")

        # Sort dict by information (either wavelength or exposure time) lowest -> highest
        self.keyImages = {k: v for k, v in sorted(self.keyImages.items())}
        return self.keyImages



    def printDict(self):
        """
        Helper function to print dictionary
        """
        for key, data_list in self.keyImages.items():
            print(f"Exposure Time: {key}")
            print(f"Number of Arrays: {len(data_list)}")
        
        # Iterate through each numpy array for the current exposure time
            for i, data in enumerate(data_list):
                print(f"Array {i + 1}")
                print(f"Data Type: {data.dtype}")
                print(f"Data Shape: {data.shape}")
                # Print a small portion of the data (e.g., the first 5x5 elements)
                small_portion = data[:5, :5]  # Adjust the indexing as needed
                print("Small Portion of Data:")
                print(small_portion)
                print("-" * 20)  # Separator between arrays
            print("=" * 30)  # Separator between exposure times