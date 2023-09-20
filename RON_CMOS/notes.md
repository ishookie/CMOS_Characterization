

For all of the images I have taken except for the -5C High/Low Gain have been with 2 binning turned on. Binning averages neighboring pixels together, allegedly reduces read noise as well as file size. This is not what we want. I want to do all the image processing myself. I re-did it for the two -5C bias folders

- redoing RON with this I get min value 0.0, max value: 19.012 Mean value: 1.404 (High Gain)

Right now for RON I find the stDEV of the vector of pixels across my N bias frames. This will include fixed pattern noise (FPN) I want to remove this and the way to do that is to remove it by subtracting bias frames from eachother then doing the same analysis. I will do this by first with only two bias frames I will subtract them 
