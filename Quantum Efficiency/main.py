from lib.Monochromator import Monochromator
from lib.Photodiode import Photodiode
from lib.dfcore import dfcore

import csv
import numpy as np
import time 



def runPhotodiode(start=400, stepSize=100):
     # Create instrument objects
    monochromator = Monochromator()
    photodiode = Photodiode() 
    
    # List for wavelengths 
    wavelengths = []
    data = [] 
    
    # Go to starting wl and wait extra long
    monochromator.goWave(start)
    time.sleep(5) 
    
    for n in range(start, 700 + stepSize, stepSize):
        wl = monochromator.goWave(n)
        wavelengths.append(wl) 
        photodiode.setWavelength(wl) 
        data.append(photodiode.readData())
        
        
        
        dirPath = '/photodiode'
        
        # Define the CSV file name
        file_name = 'example.csv'  # Replace with your desired file name

        # Combine the directory and file name to get the full file path
        filePath = f'{dirPath}/{file_name}'
        
        with open(filePath, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Power'])
            writer.writerow([timestamp, power_reading])
        
    print(f"Wavelengths: {wavelengths}")
    print(f"Data: {data}")
    

def runCamera(start=400, stepSize=100):
    monochromator = Monochromator()
    cam = dfcore()
    
    # Go to starting wl and wait extra long
    monochromator.goWave(start)
    time.sleep(5)
    
    for n in range(start, 700+stepSize, stepSize):
        wl = monochromator.goWave(n)
        time.sleep(2)
        cam.takeExposures(duration=0.0001,wavelength=n,numExposes=5)

def takeDarks():
    cam = dfcore()
    
    cam.takeDarks(1,1) 

if __name__ == '__main__':
    # m = Monochromator()
    # m.goWave(550)
    # runCamera() 
    # runPhotodiode()
    # m = Monochromator()
    # m.goWave(500) 
    # p = Photodiode()
    # p.setWavelength(500)
    # print(p.readData())
    
    takeDarks() 
    
        
        
        
        
   