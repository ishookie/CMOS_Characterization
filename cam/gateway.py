import cppyy
import cppyy.ll
import ctypes

from log import DFLog

cppyy.include('/usr/local/include/dlapi.h')
cppyy.load_library('/usr/local/lib/libdlapi')

dl = cppyy.gbl.dl

class DLAPIGatewayError(Exception):
    """Exception raised when an SBIG Gateway error occurs."

    Attributes:
        msg - error message
    """
    def __init__(self, gateway, message:str = "Camera error."):
        if gateway is not None:
            dl.deleteGateway(gateway)
        self. message = message
        super().__init__(self.message)
    pass


class DLAPIGateway(object):
    """A Diffraction Limited (SBIG) DLAPI device gateway.  
    """

    def __init__(self, verbose:bool=False):
        """Initializes the gateway object.

        Args:
            verbose (bool, optional): sets verbose mode on (True) or off (False). Defaults to False.
        """
        # Use custom logger
        self.logger = DFLog('DLAPIGateway').logger
        self.gateway = None
        
        try:
            self.logger.info('Initializing gateway.')
            self.gateway = dl.getGateway()
            self.gateway.queryUSBCameras()
            self.n_devices = self.gateway.getUSBCameraCount()
            self.devices = []
            self.serial_numbers = []
            self.device_number_dictionary = {}
            self.verbose = verbose
            
            self.logger.info('Number of cameras found: {}'.format(self.n_devices))
            serial_number_buffer = ctypes.create_string_buffer(512)
            buffer_length = ctypes.c_ulong(512)
            for i in range(self.n_devices):
                pCamera = self.gateway.getUSBCamera(i)
                pCamera.initialize()
                self.devices.append(pCamera)
                
                pCamera.getSerial(serial_number_buffer, buffer_length)
                serial_number = serial_number_buffer.value.decode()
                
                
                if 'SCE1300M' in serial_number:
                    camera_name = 'starchaser'
                elif 'AL694M' in serial_number:
                    camera_name = 'aluma'
                elif 'STC428M' in serial_number:
                    camera_name = 'stc'
                else:
                    raise DLAPIGatewayError(self.gateway, 'Unknown camera type.')
                
                self.serial_numbers.append(serial_number)
                self.device_number_dictionary[camera_name] = i
                message = 'Enumerated camera number: {} type: {} serial number: {}'.format(i, camera_name, serial_number)
                if self.verbose:
                    print(message)
                self.logger.info(message)
        except:
            raise DLAPIGatewayError(self.gateway, "Error initializing gateway.")
        
    def __del__(self):
        """Closes the gateway.
        """
        self.logger.info('Deallocating gateway.')
        dl.deleteGateway(self.gateway)
        self.gateway = None