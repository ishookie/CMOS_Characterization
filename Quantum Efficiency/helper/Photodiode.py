import serial 
import time 
import numpy as np 



class Photodiode: 
    
    def __init__(self, port="/dev/ttyUSB1"):
        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baudrate = 9600
        self.ser.bytesize = serial.EIGHTBITS # number of bits per bytes
        self.ser.parity = serial.PARITY_NONE # set parity check: no parity
        self.ser.stopbits = serial.STOPBITS_ONE # number of stop bits
        self.ser.timeout = 1 # non-block read
        self.ser.writeTimeout = 2 # timeout for write
        
        self.terminating = '\n' # Line terminators
        self.encoding = 'utf-8' # Encoding for communications
        
        # Open the serial connection
        self.open()
        time.sleep(0.5)
        # Disable Echo (messes up reading data)
        self.disableEcho()
        time.sleep(0.5)
        # Turn attenuation on
        self.attenuationOn()
        time.sleep(0.5)
        # Set Range to R4
        self.setRange()
        time.sleep(0.5)
        self.setUnits() 
        time.sleep(0.5)
        
    def __del__(self):
        self.ser.close() 
        
    def open(self):
        """
        Open serial connection.
        """
        self.ser.open() 
        return 
        
        
    def setUnits(self):
        """
        Make sure the correct unit setting is set.
        """
        self.write("U1")
        return 
        
        
    def disableEcho(self):
        """
        Checks and disables Echo mode.
        Needs to be disabled for proper flushing out output.
        """
        self.write("E?")
        response = self.ser.readline().decode(self.encoding).strip() 
        if not response:
            return
        elif response:
            self.write("E0")
        return 
    
    
    def setRange(self):
        """
        Set the measurment range.
        """
        self.write("R1")
        return 
    
        
    def attenuationOn(self):
        """
        Turn on the detector-attenuation combo.
        """
        self.write("A1")
        return 
        
        
    def write(self, msg):
        """
        Send a specified command through the serial port.

        Args:
            msg (str): Command to be sent.

        Returns:
            int: Number of bytes written. 
        """
        msg = f"{msg}{self.terminating}".encode(self.encoding)
        return self.ser.write(msg)  
    
    def writeAndRead(self, msg, display = False):
        """
        Write a message and return the response from the powermeter. 

        Args:
            msg (_type_): Command to be sent. 
            display (bool, optional): Display response message in console. Defaults to False.

        Returns:
            response (str): Response message from power meter. 
        """
        self.write(msg) 
        response = self.ser.readline().decode(self.encoding).strip() 
        if display: 
            print(response)
        return response 
        
    
    def getRange(self, display=False):
        """
        Get the current range of the powermeter and print it. 
        
        Args:
            display (bool, optional): Print response message to console. Defaults to False
        
        Returns: 
            str: current range of power meter
        """
        self.write("R?")
        response = self.ser.readline().decode(self.encoding).strip() 
        if display: 
            print(response)
        return response 
    
    
    def readData(self, display=False):     
        """
        Read data from powermeter.
        
        Returns:
            float: value of powermeter 
        """ 
        self.write("D?")  
        response = self.ser.readline().decode(self.encoding).strip() 
        return response
        
    def setWavelength(self, wl):
        """
        Set the power meter to a given wavelength.
        
        Args: 
            wl (int): desired wavelength 
        """
        self.write(f"W{wl}")
        time.sleep(0.2)
        return 


    def curWavelength(self):
        """
        Get the current wavelength setting and prints it. 
        
        Returns:
            int: Current wavelength 
        """
        self.write("W?")
        response = self.ser.readline().decode(self.encoding).strip() 
        print(response) 
        return response 
        

if __name__ == '__main__':
    test = Photodiode()
    test.open() 
    test.setWavelength(500)
    time.sleep(3)
    test.curWavelength()
    

