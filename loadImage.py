import os
import numpy as np 
from astropy.io import fits


class fitsLoader:

    images = []
    stackedImg = 0 
    signedImages = []

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
        for n in range(0, len(self.signedImages) - 1, 2):
            self.stackedImg += self.signedImages[n] - self.signedImages[n+1]
        return self.stackedImg 

    def makeInt32(self):
        for n in self.images:
            self.signedImages.append(n.astype(np.int32))
        return self.signedImages


    """
    Want to do statistics on individual pixels across multiple frames
    returns an array of pixels at a certain offset - JUST DOING [2,2] AS AN ARBITRARY STARTING VALUE
    """
    def stackPixels(self, x, y):
        # create 1D array of int32 size 10 -> maybe additional argument to choose size 
        pixel = np.empty(10, dtype=np.int32)
    
        for i, frame in enumerate(self.images):
            newElement = frame[x][y]
            pixel[i] = newElement
        
        return pixel 
    
























    def test(self):
        for n in self.images:
            print(type(n[1][2]))
            print(n[1][2])


