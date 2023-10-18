import serial 
import time 
import numpy as np 



class Photodiode: 
    
    def __init__(self):
        self.ser = serial.Serial()
        self.ser.port = "/dev/tty.usbserial-120"
        self.ser.baudrate = 9600
        self.ser.bytesize = serial.EIGHTBITS # number of bits per bytes
        self.ser.parity = serial.PARITY_NONE # set parity check: no parity
        self.ser.stopbits = serial.STOPBITS_ONE # number of stop bits
        self.ser.timeout = 1 # non-block read
        self.ser.writeTimeout = 2 # timeout for write
        
        self.terminating = '\n' # Line terminators
        self.encoding = 'utf-8' # Encoding for communications
        
        self.wavelengths = np.empty((0,))
    
    def disableEcho(self):
        """
        Checks and disables Echo mode.
        needs to be disabled for proper flushing out output
        """
        
        self.write("E?")
        response = self.ser.readline().decode(self.encoding).strip() 
        if not response:
            return
        elif response:
            self.write("E0")
            
        return 
        
        
    def open(self):
        """
        Open serial connection 
        """
        self.ser.open() 
        self.disableEcho()
        
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
    
    def getRange(self):
        
        self.write("R?")
        response = self.ser.readline().decode(self.encoding).strip() 
        print(response) 
        
    
    
    def readData(self):     
        """
        
        """ 
        self.write("D?")  
        response = self.ser.readline().decode(self.encoding).strip() 
        print(response) 
        
    def setWavelength(self, wl):
        self.write(f"W{wl}")
        time.sleep(0.2)
        return 

    def curWavelength(self):
        self.write("W?")
        response = self.ser.readline().decode(self.encoding).strip() 
        print(response) 
        return
        

if __name__ == '__main__':
    test = Photodiode()
    test.open() 
    test.setWavelength(500)
    time.sleep(3)
    test.curWavelength()