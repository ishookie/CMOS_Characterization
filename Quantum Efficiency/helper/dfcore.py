import subprocess 


class dfcore: 
    
    def __init__(self):
        self.path = "./helper/dfcore"
        # Cooling off by default
        self.coolingOff()
        # Directories for saving images
        self.saveDir = 'data/exposures'
        self.saveDirDarks = 'data/darks'
    
    
    def coolingOff(self):
        """
        Disable cooling of camera. 
        """
        arguments = ["cool", "disable"]
        self.sendCommand(arguments)
        return 
        
    
    def sendCommand(self, arguments):
        """
        Run dfcore with specified arguments
        *arguments are in the form of a list, example:
        ["expose", "--duration", "0.1", "--disable_overscan", "1"]
        """
        command = [self.path] + arguments
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        # Error handling
        if process.returncode != 0:
            print(f"Error Running dfcore code: {process.returncode}")
        if stderr: 
            print(f"Error: {stderr.decode()}")
        
    
    def takeExposures(self, duration = 0, wavelength=0, numExposes=0):
        """
        Take an exposure. 
        
        Args: 
            duration (float): Exposure duration 
            wavelength (int): Wavelength exposure taken at (used for file naming)
            numExposes: (int): number of exposures to be taken. 
        """
        # Error handling 
        if wavelength == 0:
            print("Error: please provide filename (wavelength)")
        elif numExposes == 0:
            print("Error: please provide number of exposures")
        elif duration == "0":
            print("Error: please provide exposure duration")
        
        # Compose initial arguments
        arguments = ["expose", "--duration", str(duration), "--disable_overscan", "1", "--camera", "0", "--savedir", str(self.saveDir)]
        
        # Take exposures and name files accordingly
        for n in range(numExposes):
            command = arguments + ["--filename", f"{wavelength}nm_{duration}s_{n}.fits" ]
            self.sendCommand(command)
            command = [] 
            

    def takeDarks(self, duration=0, numDarks=0):
        if numDarks == 0:
            print("Error: please provide number of darks to be taken")
        
        arguments = ["expose", "--duration", str(duration), "--disable_overscan", "1", "--camera", "0", "--dark", "--savedir", str(self.saveDirDarks)]
        
        for n in range(numDarks):
            command = arguments + ["--filename", f"{duration}s_{n}.fits" ]
            self.sendCommand(command)
            command = [] 
        
    def setTemp(self, temp):
        """
        INCOMPLETED NOT SURE ABOUT TEMP & QE
        - set target temp then wait till "cool get" stdout returns correct temp within range
        """
        arguments = ["cool", "get"]
        command = [self.path] + arguments
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        stdout, stderr = process.communicate() 
        
        print(f"stdout: {stdout} stderr {stderr}")

         
    
        
        