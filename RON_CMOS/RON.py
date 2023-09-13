import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.visualization import astropy_mpl_style
import numpy as np
import math
import os

import loadImage

plt.style.use(astropy_mpl_style)

# Name of folder containing images
relativePath = '12.8C' 

# constant offset so pixel values are non-zero after subtraction
offset = 10

# get path of image folder
absPath = os.path.dirname(__file__)
fullPath = os.path.join(absPath, relativePath)

# create instance of loadImage class called 'fitsLoader' 
fitsLoader = loadImage.fitsLoader(fullPath)
#load Image
fitsLoader.loadImages()

# Subtract N frames from eachother
stackedImg = fitsLoader.stackFrames()

fitsLoader.test()

# print(type(stackedImg))
# print(stackedImg[1][1])
# print(stackedImg[2][3])


stackedOffset = stackedImg + offset




print(f"no offset: \n{stackedImg[1:6,1:6]}")
print(f"w/ offset: \n{stackedOffset[1:6,1:6]}")

print(f"min: {np.min(stackedOffset)}")
print(f"max {np.max(stackedOffset)}")

stdev = np.std(stackedOffset)
final = stdev/math.sqrt(2) 

print(final) 

# #calculate difference of bias frames as a function of their standard deviation
# #constant added after subtraction so values are all non-zero
# stdev = np.std(inter)
# final = stdev/math.sqrt(2)

# print(final)




# # print(image_data.shape)

# fig, (ax0, ax1) = plt.subplots(nrows=2)

# # plt.imshow(data2, cmap='gray')

# # 
