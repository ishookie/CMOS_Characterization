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
    data = {} 
    
    # Directory where data will be saved
    dirPath = '/photodiode'
    
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
            
        data[wl] = readings 
        data.append(photodiode.readData())
        
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

def takeDarks(start = 400, stepSize=100):
    cam = dfcore()
    
    for n in range(start, 700+stepSize, stepSize):
        cam.takeDarks(0.0001 ,numDarks=5)
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
    
        
        
        
        
   