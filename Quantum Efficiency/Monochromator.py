import serial 
import time 
import numpy as np 



class Monochromator:
    
    def __init__(self):
        self.ser = serial.Serial()
        self.ser.port = "/dev/tty.usbserial-1140"
        self.ser.baudrate = 9600
        self.ser.bytesize = serial.EIGHTBITS #number of bits per bytes
        self.ser.parity = serial.PARITY_NONE #set parity check: no parity
        self.ser.stopbits = serial.STOPBITS_ONE #number of stop bits
        self.ser.timeout = 1            #non-block read
        self.ser.writeTimeout = 2     #timeout for write
        
        self.terminating = '\r\n'
        self.encoding = 'utf-8'
        
        self.wavelengths = np.empty((0,))
        
    
    def __del__(self):
        self.ser.close() 
        
    def open(self):
        """
        Open serial connection 
        """
        self.ser.open() 
    
    def units(self):
        msg = f"SHUTTER C{self.terminating}".encode(self.encoding)
        return self.ser.write(msg)   
    
    def customCommand(self, msg):
        """
        Send a sepcified command through the serial port

        Args:
            msg (str): The command to be sent
        """
        msg += self.terminating
        msg = msg.upper()
        msg = msg.encode(self.encoding)
        return self.ser.write(msg)

    def write(self, msg):
        """
        Send a sepcified command through the serial port

        Args:
            msg (str): Command to be sent

        Returns:
            int: Number of bytes written. 
        """
        msg = f"{msg}{self.terminating}".encode(self.encoding)
        return self.ser.write(msg)  
    
    
    def openShutter(self):
        """
        Opens the shutter on the device. 
        """
        return self.write("SHUTTER O") 
    
    
    def closeShutter(self):
        """
        Closes the shutter on the device. 
        """
        return self.write("SHUTTER C")
    
    
    def goWave(self, waveLength):
        """
            Go to specified wavelength.

        Args:
            waveLength (int): Desired wavelength

        Returns:
            float: current wavelength
        """
        self.write(f"GOWAVE {waveLength}")
        time.sleep(3) 
        self.write("WAVE?")
        # Super scuffed way of getting most recent response 
        # Could also use a separate thread to keep track but I AM LAZY!>!>!
        self.ser.readline()
        self.ser.readline()
        response = self.ser.readline().decode(self.encoding).strip() 
        return response
    
    def readWavelength(self):
        self.write("WAVE?")
        time.sleep(3) 
        response = self.ser.readline().decode(self.encoding)
        print(response)
    
    
    def sweepVisible(self, stepSize):
        """_summary_

        Args:
            stepSize (_type_): _description_
        """
        # start at 400nm wavelength 
        start = 400 
        self.goWave(start)
        #Longer sleep at the start
        time.sleep(5) 
        
        for i in range(start, 700 + stepSize, stepSize):
            wl = self.goWave(i)
            self.wavelengths = np.append(self.wavelengths, wl)
        
        print(self.wavelengths)


if __name__ == '__main__':
    test = Monochromator() 
    test.open() 
    test.goWave(550)