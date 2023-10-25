from helper.Monochromator import Monochromator
from helper.Photodiode import Photodiode
from helper.dfcore import dfcore

import csv
import numpy as np
import time 



def runPhotodiode(start=400, stepSize=100):
     # Create instrument objects
    monochromator = Monochromator()
    photodiode = Photodiode() 
    
    # List for wavelengths 
    wavelengths = []
    data = {} 
    
    # Directory where data will be saved
    dirPath = 'data/photodiode'
    
    # Go to starting wl and wait extra long
    monochromator.goWave(start)
    time.sleep(5) 
    
    for n in range(start, 700 + stepSize, stepSize):
        wl = monochromator.goWave(n)
        wavelengths.append(wl) 
        photodiode.setWavelength(wl) 
        
        readings = [] 
        
        # Get 5 minutes of readings in 1s intervals
        for i in range(300):
            readings.append(photodiode.readData()) 
            time.sleep(1) 
            
        if wl not in data:
            data[wl] = []
        
        data[wl] = readings
        
        # Define the CSV file name
        file_name = 'example.csv'  # Replace with your desired file name
        filePath = f'{dirPath}/{file_name}'
        
        # Write csv file 
        with open(filePath, 'w', newline='') as file:
            csv_writer = csv.writer(file)
            # Write the header row with column names
            csv_writer.writerow(['Wavelength', 'Readings'])
            # Write data
            for wavelength, readings in data.items():
                for reading in readings:
                    csv_writer.writerow([wavelength, reading])
        
    print(f"Wavelengths: {wavelengths}")
    print(f"Data: {data}")
    

def runCamera(duration, start=400, stepSize=100):
    monochromator = Monochromator()
    cam = dfcore()
    
    # Go to starting wl and wait extra long
    monochromator.goWave(start)
    time.sleep(5)
    
    for t in duration: 
        for n in range(start, 700+stepSize, stepSize):
            wl = monochromator.goWave(n)
            time.sleep(2)
            cam.takeExposures(t,wavelength=n,numExposes=5)

def takeDarks(start = 400, stepSize=100):
    cam = dfcore()
    
    for n in range(start, 700+stepSize, stepSize):
        cam.takeDarks(0.0001 ,numDarks=5)
    cam.takeDarks(1,1) 

if __name__ == '__main__':
    m = Monochromator()
    m.openShutter()
    m.goWave(550) 
    
    # duration = [1,3,5]
    # runCamera(duration) 
    # runPhotodiode() 
    
        
        
        
        
   