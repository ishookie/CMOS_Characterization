from helper.Monochromator import Monochromator
from helper.Photodiode import Photodiode
from helper.dfcore import dfcore

import sys 
sys.path.append("../cam")
from camera import DLAPICamera
from gateway import DLAPIGateway


import csv
import numpy as np
import time 

def runPhotodiode(start=400, stepSize=100, file_name = 'photodiodeData'):
    """
    Gather photodiode readings. Initial wavelength at start and goes till 700 + stepSize.
    data is saved as a csv in data/photodiode.

    Args:
        start (int, optional): Starting wavelength in nm. Defaults to 400.
        stepSize (int, optional): Wavelength stepsize in nm. Defaults to 100.
        file_name (str, optional): filename for saved data. In csv format. Defaults to 'photodiodeData'.
    """
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
        time.sleep(1)
        
        readings = [] 
        
        # Get 5 minutes of readings in 1s intervals
        for i in range(300):
            readings.append(photodiode.readData()) 
            time.sleep(1) 
            
        if wl not in data:
            data[wl] = []
        
        data[wl] = readings
        
        # Define the CSV file name
        file_name += '.csv'  
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
    print("Photodiode Readings Finished :)")
    return
    
    
def photodiodeDark(start=400, stepSize = 100, file_name = 'photodiode_dark'):
    """
    Take photodiode readings.

    Args:
        start (int, optional): Wavelength setting start. Defaults to 400.
        stepSize (int, optional): Wavelength setting step size. Defaults to 100.
        file_name (str, optional): csv filename. Defaults to 'photodiode_dark'.
    """
    # Create instrument objects
    monochromator = Monochromator()
    photodiode = Photodiode() 
    
    # List for wavelengths 
    wavelengths = []
    data = {} 
    
    # Directory where data will be saved
    dirPath = 'data/photodiode'
    
    for n in range(start, 700 + stepSize, stepSize):
        photodiode.setWavelength(next) 
        time.sleep(1)
        readings = [] 
        
        # Get 5 minutes of readings in 1s intervals
        for i in range(300):
            readings.append(photodiode.readData()) 
            time.sleep(1) 
            
        if n not in data:
            data[n] = []
        data[n] = readings
        # add csv extension to filename
        file_name += '.csv'  
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
        

## ADD CAMERA MODE HERE***
def runCamera(duration, start=400, stepSize=100):
    """
    Take camera exposures.

    Args:
        duration (list[3]): Exposure duration in seconds, maximum of 3 durations per measurment. 
        start (int, optional): Starting wavelength. Defaults to 400.
        stepSize (int, optional): Wavelength stepsize. Defaults to 100.
    """
    monochromator = Monochromator()
    
    gateway = DLAPIGateway() 
    cam = DLAPICamera(gateway, model='stc', dirname='/home/deb/Documents/CMOS_Characterization/Quantum Efficiency/data/exposures')
    cam.connect() 

    # Go to starting wl and wait extra long
    monochromator.goWave(start)
    time.sleep(5)
    for t in duration: 
        for n in range(start, 700+stepSize, stepSize):
            wl = monochromator.goWave(n)
            time.sleep(2)
            cam.expose(exptime=t, imtype='light', readout_mode='Low Gain', filename=f"{t}s_light_{n}nm_{readout_mode}.fits") 
            #cam.takeExposures(t,wavelength=n,numExposes=5)

def takeDarks(duration, numExposes=5, readout_mode='Low Gain'):
    """
    Take camera darks with specified duration and number of frames at each duration.

    Args:
        duration (list): list of exposure durations to take. 
        numExposes (int, optional): Number of exposures to take at each duration. 
    """
    gateway = DLAPIGateway() 
    cam = DLAPICamera(gateway, model='stc', dirname='/home/deb/Documents/CMOS_Characterization/Quantum Efficiency/data/exposures')
    cam.connect() 
    
    for t in duration: 
        for n in range(numExposes):
            cam.expose(exptime=t, imtype='dark', readout_mode=readout_mode, filename=f"{t}s_dark_{n}nm_{readout_mode}.fits") 
    print("Done taking darks.")
    return 

if __name__ == '__main__':

    # gateway = DLAPIGateway() 
    # cam = DLAPICamera(gateway, model='sbig', dirname='/home/deb/Documents/CMOS_Characterization/Quantum Efficiency/data/exposures')
    # cam.connect() 
    # obj = cam.expose(1)
    dur = [0.1, 0.2,0.3]
    runCamera(dur) 

    
    # ***Take Cam exposures***
    
    
    
    # exp = [12,12,12]
    # runCamera(exp)
    
    
    # m = Monochromator()
    # cam = dfcore()
    # p = Photodiode()
     
    
    # m.openShutter()
    # m.goWave(700) 
    
    # time.sleep(2)
    
    # cam.takeExposures()
    
    
    
    
    # p = Photodiode()
    # readout = p.readData()
    # print(readout)
    
    # duration = [7,10,12]
    # photodiodeDark() 
    # runCamera(duration) 
    # runPhotodiode() 
    
        
        


        
   