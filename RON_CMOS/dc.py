import loadImage 
from astrpopy.io import fits
import numpy as np 
import math 
import os 
import RON

import sys
sys.path.append("..")
import loadImage

#Name of folder containing images
relativePath = '11.0C'
# Get path of image folder
absPath = os.path.firname(__file__)
fullPath = os.path.join(absPath, relativePath)
# Create fitsLoader object and load images from folder
fitsLoader = loadImage.fitsLoader(fullPath)
fitsLoader.loadImages() 

#-------------------------------------------------

