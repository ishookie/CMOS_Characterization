import os
import numpy as np 
from astropy.io import fits


class fitsLoader:

    images = []
    stackedImg = 0 

    def __init__(self, folderPath):
        self.folderPath = folderPath


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

    """
    Takes the list of frames called "images" and subracts them as follows:

    D = D1-D2 + D3-D4 + ... + Dn-1 - Dn

    must be an even number of frames. 
    """
    def stackFrames(self):
        for n in range(0, len(self.images) - 1, 2):
            self.stackedImg += self.images[n] - self.images[n+1]
        return self.stackedImg 

    def test(self):
        for n in self.images:
            print(type(n[1][2]))
            print(n[1][2])


