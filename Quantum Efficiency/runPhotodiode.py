from Monochromator import Monochromator
from Photodiode import Photodiode
import numpy as np

import time 




if __name__ == '__main__':
    monochromator = Monochromator()
    photodiode = Photodiode() 
    
    # List for wavelengths 
    wavelengths = []
    
    # Starting Wavelength in nm 
    start = 400 
    
    # Step size of wavelength sweep in nm(?)
    stepSize = 100
    
    # Go to starting wl and wait extra long
    monochromator.goWave(start)
    time.sleep(5) 
    
    for n in range(start, 700 + stepSize, stepSize):
        wl = monochromator.goWave(n)
        wavelengths.append(wl) 
        
        photodiode.setWavelength(wl) 
        
        
        
   