import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.visualization import astropy_mpl_style
import numpy as np
import math
import os

import loadImage

#plt.style.use(astropy_mpl_style)

# Name of folder containing images
relativePath = '12.8C' 

# get path of image folder
absPath = os.path.dirname(__file__)
fullPath = os.path.join(absPath, relativePath)

# create instance of loadImage class called 'fitsLoader' 
fitsLoader = loadImage.fitsLoader(fullPath)
#load Image
fitsLoader.loadImages()

#------------------------------------------------------------

# create np array same shape different type
stdArray = np.empty_like(fitsLoader.images[0], dtype=np.float64)
pixelArray = np.empty(10, dtype=np.int32)
total = 0

"""
returns a 1D array of length N
Contains the pixel value at a (x,y) coordinate for N frames
"""
def retrievePixels(x, y):
    for i, img in enumerate(fitsLoader.images):
        newElement = img[y][x]
        pixelArray[i] = newElement
    return pixelArray 

"""
find rms of pixel array
"""
def calcRMS(arr):               # Sqrt(N)? 
    return np.std(arr) / math.sqrt(2)  



def calcPixelRMS():
    rows, cols = fitsLoader.images[0].shape
    for y in range(rows - 1):
        for x in range(cols - 1):
            pix = retrievePixels(x,y)
            rms = calcRMS(pix) 
            stdArray[y][x] = rms 
    return stdArray

stdArray = calcPixelRMS()

print(np.min(stdArray))
print(np.max(stdArray))


fig, (ax1, ax2) = plt.subplots(1,2, figsize=(10,5))

heatmap = ax1.imshow(stdArray, cmap='jet', aspect='auto')
ax1.set_title('RMS Heatmap')
plt.colorbar(heatmap, ax=ax1)

stdArray_flat = stdArray.flatten()

ax2.hist(stdArray_flat, bins=200)
ax2.set_title('RMS Histogram')
ax2.set_xlabel('RMS Values (ADU)')
ax2.set_ylabel('log(count)')
ax2.set_yscale('log')

plt.tight_layout()
plt.show() 


