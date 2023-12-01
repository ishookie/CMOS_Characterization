import os
import time
import cppyy
import cppyy.ll
import ctypes
import time
import hashlib
import numpy as np
import threading
import signal
import sys
import re

from datetime import datetime, timedelta
from astropy.io import fits



from gateway import DLAPIGateway
from log import DFLog
from base import DCPHardware

cppyy.include('/usr/local/include/dlapi.h')
cppyy.load_library('/usr/local/lib/libdlapi')

dl = cppyy.gbl.dl
    

class DLAPICameraError(Exception):
    """Exception raised when a camera error occurs. Used internally; external responses to publicmethods always return an object."

    Attributes:
        message - error message
    """
    
    def __init__(self, message:str = "Camera error."):
        self. message = message
        super().__init__(self.message)
    pass


class DLAPICameraResponse():
    def __init__(self,success:bool=True,description:str=None,payload:dict=None,warnings:list=None):
        self.success = success 
        self.description = description 
        self.payload = payload
        self.warnings = warnings


class DLAPICamera(DCPHardware):
    """A Diffraction Limited (SBIG) camera.  
    """

    def __init__(self, gateway:DLAPIGateway, model:str="stc",  dirname:str="/home/deb/Documents/CMOS_Characterization/Quantum Efficiency", 
                verbose:bool=False):
        """Initializes the DLAPICamera object.

        Args:
            gateway (DLAPIGateway): A DLAPIGateway object.
            model (str, optional): Camera model ("aluma" or "starchaser"). Defaults to "aluma".
            dirname (str, optional): Directory where images are stored. Defaults to "/tmp".
            verbose (bool, optional): Display additional messages. Defaults to False.

        Raises:
            DLAPICameraError: Error raised when a camera error occurs.
        """
        self.gateway = gateway
        self.model = model
        self.dirname = dirname
        self.verbose = verbose
        
        self.camera = None
        self.sensor = None
        self.serial_number = None
        
        # Sensor properties. These are permanent, and set when the camera connects.
        self._npix_x = None
        self._npix_y = None
        self._min_cooler_setpoint = None
        self._max_cooler_setpoint = None
        self._min_exposure_duration = None
        self._pixel_size_x = None
        self._pixel_size_y = None
        
        # Subframe properties. Set upon connection, but they can be changed by the user.
        self._top = 0
        self._left = 0
        self._width = 0
        self._height = 0
        self._bin_x = 0
        self._bin_y = 0
        
        # Define the state structure. This will get reported on by the get_status() method,
        # which gets periodically called by the polling thread.
        self._state = {}     
        self._state['camera_model'] = model.lower()
        
        if "aluma" in self._state['camera_model']:
            self._state['supports_cooling'] = True
            self._state['supports_overscan'] = True
        elif "starchaser" in self._state['camera_model']:
            self._state['supports_cooling'] = False
            self._state['supports_overscan'] = False
        elif "stc" in self._state['camera_model']:
            self._state['supports_cooling'] = True
            self._state['supports_overscan'] = False
        else:
            raise DLAPICameraError("Error. Unknown camera model.")
        
        self._state['setpoint_temperature_c'] = None
        self._state['binning'] = 1
        self._state['include_overscan'] = None
        self._state['power_draw_percent'] = None
        self._state['sensor_temperature_c'] = None
        self._state['heatsink_temperature_c'] = None
        self._state['cooling_enabled'] = None 
        self._state['is_connected'] = False
        self._state['is_exposing'] = False
                        
        # Variables describing the exposure currently in progress.
        self._imtype = None
        self._is_exposing = None
        self._exposure_duration = None
        self._exposure_start_datetime = None
        self._exposure_start_time = None
        self._exposure_mid_time = None
        self._exposure_end_time = None
        self._checksum = None
        self._automatic_filename = None
        self._next_image_number = None
        self._next_image_type = None

        self._image_stack = []
        self._latest_image = None
        self._latest_image_number = None

        # Polling
        self._polling_thread = None
        self._polling_interval = 30
        self._polling_enabled = False
        self._stop_polling = threading.Event()
        self._activity_lock = threading.Lock()
        
        # Add signal handler for SIGINT signal
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Add custom logger
        self.logger = DFLog(f'DLAPICamera({model})').logger


    @property
    def state(self):
        """General summary of the state of the DLAPI camera.

        Returns:
            state (dict): Dictionary with state information.
        """
        return self._state
    
    
    @property
    def exposure_start_time(self):
        """Time the last exposure was started.

        Returns:
            time (ctime): Time the last exposure was started.
        """
        return time.ctime(self._exposure_start_time)

    
    @property
    def latest_image(self):
        """Path to the latest FITS file generated by the camera.

        Returns:
            path (str): Path to the latest FITS file generated by the camera.
        """
        return self._latest_image

    
    @property
    def image_stack(self):
        """List of FITS files generated by the camera.

        Returns:
            imstack (list): List of images generated since the camera was connected.
        """
        return self._image_stack


    def connect(self):
        """Connects to the DLAPI camera.

        Raises:
            DLAPICameraError: Error raised if the camera cannot be connected to.
        """
        try:
            self.logger.info("Connecting to camera.")
            camnum = self.gateway.device_number_dictionary[self.model]
            self.camera = self.gateway.devices[camnum]
            self.sensor = self.camera.getSensor(0)
            self.serial_number = self.gateway.serial_numbers[camnum]
            handlePromise(self.sensor.abortExposure())
            time.sleep(0.5)

            info = self.sensor.getInfo() 
            self._npix_x = info.pixelsX
            self._npix_y = info.pixelsY
            self._min_cooler_setpoint = info.minCoolerSetpoint
            self._max_cooler_setpoint = info.maxCoolerSetpoint
            self._min_exposure_duration = info.minExposureDuration
            self._pixel_size_x = info.pixelSizeX
            self._pixel_size_y = info.pixelSizeY
        except:
            return DLAPICameraResponse(success=False,description="Could not connect to camera.")
        
        highnum = highest_fits_sequence_number(self.serial_number, self.dirname)
        if highnum is None:
            highnum = 0
        self._latest_image_number = highnum
        
        self._state['is_connected'] = True
        self.set_default_subframe()
        time.sleep(0.5)
        self.logger.info("Camera is connected.")
        return DLAPICameraResponse(success=True,description="Camera Connected Successfully.")

    def disconnect(self):
        """Disconnects the DLAPI camera.
        """
        try:
            self.logger.info("Disconnecting camera.")
            self.camera = None
            self.sensor = None
            self.serial_number = None
            self._state['is_connected'] = False
            return DLAPICameraResponse(success=True,description='Camera Disconnected Successfully.')
        except:
            return DLAPICameraResponse(success=False,description="Could not disconnect from camera.")     
        
    @property
    def is_connected(self):
        """Checks if the camera is connected.

        Raises:
            DLAPICameraError: Error that occurs when the camera is not connected.
        """
        if not self._state['is_connected']:
            return DLAPICameraResponse(success=False,description="Error. Camera not connected.")
        else:
            return DLAPICameraResponse(success=True,description="Camera is Connected.")
    @property 
    def _is_connected(self)->bool:
        return self._state['is_connected']
    
    def check_connected(self):
            if not self._state['is_connected']:
                try:
                    self.connect() 
                except:
                    raise DLAPICameraError('Not Connected and could not connect.')

    
    def _get_sensor_info(self):
        """Returns general information for the sensor.

        Returns:
            Dictionary with information.
        """
        self.check_connected()
        self.sensor.queryInfo()
        info = self.sensor.getInfo()
        output = {}
        output['exposure_precision'] = info.exposurePrecision
        output['filter_type'] = info.filterType
        output['flag'] = info.flag
        output['frame_type'] = info.frameType
        output['has_rbi_preflash'] = info.hasRBIPreflash
        output['id'] = info.id
        output['max_bin_x'] = info.maxBinX
        output['max_bin_y'] = info.maxBinY
        output['max_cooler_setpoint'] = info.maxCoolerSetpoint
        output['min_cooler_setpoint'] = info.minCoolerSetpoint
        output['min_exposure_duration'] = info.minExposureDuration
        output['model'] = info.model
        output['number_of_channels_available'] = info.numberOfChannelsAvailable
        output['pixel_size_x'] = info.pixelSizeX
        output['pixel_size_y'] = info.pixelSizeY
        output['pixelsX'] = info.pixelsX
        output['pixelsY'] = info.pixelsY
        return output
        #return DLAPICameraResponse(description='sensor info',payload=output)
    
    def get_sensor_info(self):
        try:
            info = self._get_sensor_info()
            return  DLAPICameraResponse(description='sensor info',payload=info)
        except:
            return DLAPICameraResponse(success=False,description='sensor info not obtained')

    def _get_sensor_calibration(self):
        """Returns the sensor calibration information.

        Returns:
            Dictionary with information.
        """
        self.check_connected()
        self.sensor.queryCalibration()
        info = self.sensor.getCalibration()
        output = {}
        output['adc_gains'] = info.adcGains
        output['adc_offsets'] = info.adcOffsets
        output['channels_in_use'] = info.channelsInUse
        output['electronic_gain'] = info.eGain
        output['substrate_voltage'] = info.substrateVoltage
        return output
        #return DLAPICameraResponse(description='sensor calibration',payload=output)
    def get_sensor_calibration(self):
        try:
            info = self._get_sensor_calibration()
            return  DLAPICameraResponse(description='sensor calibration',payload=info)
        except:
            return DLAPICameraResponse(success=False,description='sensor calibration not obtained')

    def set_polling_interval(self, seconds):
        """Sets the polling interval.

        Args:
            seconds (int): Polling interval in seconds.
        """
        self.logger.info(f"Setting polling interval to {seconds} seconds.")
        self._polling_interval = seconds
        return DLAPICameraResponse(description=f"polling interval set to {seconds}")

    
    def set_default_subframe(self):
        """Sets the subframe to the full unbinned frame.

        Raises:
            DLAPICameraError: Error raised if the subframe cannot be restored to the default.
        """
        if not self._state['is_connected']:
            return DLAPICameraResponse(success=False,description="Error. Camera not connected.")
        try:
            self._top = 0
            self._left = 0
            self._width = self._npix_x
            self._height = self._npix_y
            self._bin_x = 1
            self._bin_y = 1
            self.set_subframe(self._top, self._left, self._width, self._height, 
                            self._bin_x, self._bin_y)
            return DLAPICameraResponse(success=True,description="Success, set subframe to default.")
        except:
            return DLAPICameraResponse(success=False,description="Error. Could not set default subframe.")     


    def set_subframe(self, top:int, left:int, nx:int, ny:int, binx:int, biny:int) -> None:
        """Sets the camera subframe parameters (position, size, and binning).

        Args:
            top (int): Pixel position of the top of the subframe
            left (int): Pixel position of the left of the subframe
            nx (int): Number of pixels in the x direction
            ny (int): Number of pixels in the y direction
            binx (int): Binning factor
            biny (int): Binning factor
        """
        if not self._state['is_connected']:
            return DLAPICameraResponse(success=False,description="Error. Camera not connected.")
        with self._activity_lock:
            try:
                if self.verbose:
                    self.logger.info("Setting subframe to top={}, left={}, nx={}, ny={}, binx={}, biny={}".format(top, left, nx, ny, binx, biny))
                self._top = top
                self._left = left
                self._width = nx
                self._height = ny
                self._bin_x = binx
                self._bin_y = biny
                subf = dl.TSubframe(top, left, nx, ny, binx, biny)
                handlePromise(self.sensor.setSubframe(subf))
                return DLAPICameraResponse(description="subframe set.")
            except:
                return DLAPICameraResponse(success=False,description="Error. Could not set default subframe.")  


    def _get_readout_modes(self):
        """Get a list of available readout modes.

        Returns:
            modes (list[str]): List of readout modes.
        """
        if not self._state['is_connected']:
            return DLAPICameraResponse(success=False,description="Error. Camera not connected.")
        with self._activity_lock:
            readout_modes_buffer = ctypes.create_string_buffer(1024)
            buffer_length = ctypes.c_ulong(1024)
            self.sensor.getReadoutModes(readout_modes_buffer, buffer_length)
            readout_modes = readout_modes_buffer.value.decode()
            return readout_modes.split('\n')
            
    def get_readout_modes(self):
        try:
            readout_modes = self._get_readout_modes()
            return DLAPICameraResponse(description='readout modes',payload={'readout modes':readout_modes})
        except:
            return DLAPICameraResponse(success=False,description='readout modes could not be obtained')

    
    def set_temperature(self, setpoint):
        """Sets the temperature setpoint of the camera. (Does not automatically cool the camera.)

        Args:
            setpoint (float): Temperature setpoint for the camera (in degrees C)

        Raises:
            DLAPICameraError: Error thrown if the temperature setpoint cannot be set.
        """
        if not self._state['is_connected']:
            return DLAPICameraResponse(success=False,description="Error. Camera not connected.")
        with self._activity_lock:
            if self._state['supports_cooling']:
                cooler = self.camera.getTEC()
                cooler_is_enabled = cooler.getEnabled()
                self._state['setpoint_temperature_c'] = setpoint
                handlePromise(cooler.setState(cooler_is_enabled, setpoint))
                self._state['cooling_enabled'] = True
                return DLAPICameraResponse(success=True,description="Cooling setpoint set. (cooling not yet active).")
            else:
                return DLAPICameraResponse(success=False,description="Error. Camera does not support cooling.")


    def start_cooling(self, setpoint=None):
        """Activate thermoelectric cooling.

        Args:
            setpoint (float, optional): Setpoint in degrees C. Defaults to None, in which case the stored setpoint is used.

        Raises:
            DLAPICameraError: Error raised if cooling cannot be started.
        """
        if not self._state['is_connected']:
            return DLAPICameraResponse(success=False,description="Error. Camera not connected.")
        with self._activity_lock:
            if self._state['supports_cooling']:
                cooler = self.camera.getTEC()
                if setpoint is None:
                    setpoint = float(self._state['setpoint_temperature_c'])
                handlePromise(cooler.setState(True, setpoint))
                self._state['cooling_enabled'] = True
                return DLAPICameraResponse(success=True,description="Cooling Enabled.")
            else:
                return DLAPICameraResponse(success=False,description="Error. Camera does not support cooling.")

        
    def stop_cooling(self):
        """Stops thermoelectric cooling.

        Raises:
            DLAPICameraError: Error thrown if cooling cannot be stopped.
        """
        if not self._state['is_connected']:
            return DLAPICameraResponse(success=False,description="Error. Camera not connected.")
        with self._activity_lock:
            if self._state['supports_cooling']:
                cooler = self.camera.getTEC()
                setpoint = float(self._state['setpoint_temperature_c'])
                handlePromise(cooler.setState(False, setpoint))
                self._state['cooling_enabled'] = False
                return DLAPICameraResponse(success=True,description="Cooling Disabled.")
            else:
                return DLAPICameraResponse(success=False,description="Error. Camera does not support cooling.")


    def expose(self, exptime:float, 
                imtype:str = "light", 
                filename:str = None, 
                readout_mode:str ='Low Gain', 
                fast:bool = False,
                use_preflash:bool = False, 
                use_external_trigger:bool = False, 
                checksum = False, 
                debug:bool = False, 
                wait=True):
        """Exposes the DLAPI Camera.

        Args:
            exptime (float): Exposure time in seconds
            imtype (str, optional): Type of image ("bias", "dark", "flat", or "light"). Defaults to "light"
            filename (str, optional): FITS filename to output. Defaults to None, in which case a standard name is applied
            readout_mode (str, optional): Image readout mode. Defaults to 'Normal'. See get_readout_modes() for the list of available modes.
            use_preflash (bool, optional): Apply image preflash? Defaults to False.
            use_external_trigger (bool, optional): Use external trigger? Defaults to False.
            checksum (bool, optional): Compute checksum of image data portion and write it to the log. Defaults to False.
            debug (bool, optional): Print addtional information. Defaults to False.
            wait (bool, optional): Block until completed. Defaults to True.

        Raises:
            DLAPICameraError: Error raised if exposure cannot be taken.
        """
        # Make sure we are connected before trying to expose
        if not self._state['is_connected']:
            return DLAPICameraResponse(success=False,description="Error. Camera not connected.")

        # Figure out the filename
        self._imtype = imtype
        if not filename:
            self._automatic_filename = True
            sequence_number = self._latest_image_number + 1
            filename = self.serial_number + "_" + str(sequence_number) + "_" + imtype + ".fits"
            self._next_filename = os.path.join(self.dirname, filename)
        else:
            self._automatic_filename = False
            self._next_filename = os.path.join(self.dirname, filename)

        # Do we want to open the shutter?
        if ("dark" in imtype.lower()) or ("bias" in imtype.lower()):
            open_shutter = False
        else:
            open_shutter = True
            
        # Get the index of the desired readout mode.
        try:
            readout_mode_index = self._get_readout_modes().index(readout_mode)
        except ValueError:
            return DLAPICameraResponse(success=False,description=f"Error. Readout mode '{readout_mode}' not supported.")
        # If we're not in fast mode, abort any exposure that might be in progress.
        # This shouldn't be necessary bit it seems to have the side-effect of 
        # clearing the buffer and lowering read noise.
        if not fast:
            self.abort_exposure()
        try:
            with self._activity_lock:
                self._is_exposing = True
                self._state['is_exposing'] = True
                if debug:
                    print("Starting exposure with call to _start_exposure().")
                self._start_exposure(exptime, open_shutter=open_shutter, readout_mode=readout_mode_index, 
                                    use_preflash=use_preflash, use_external_trigger=use_external_trigger)
                
            # If we don't want to wait for the exposure to complete, return now.
            if not wait:
                return DLAPICameraResponse(success=True,description="Exposure Started (non blocking).")
            
            # Wait for the exposure to complete.
            if debug:
                print("Sleeping until exposure time has elapsed.")
            time.sleep(exptime)
            
            # Time's up! But we might need to wait a little longer, as the camera
            # might need to move the image into the buffer. So wait for that to
            # finish.
            if debug:
                print("Checking if exposure is finished.")
            try:
                with self._activity_lock:
                    self._wait_for_exposure_to_complete(debug=debug)
            except DLAPICameraError:
                self.logger.error("Attempting to get image data anyway.")
                pass
            
            # Get the status so the latest temperature information gets written to the 
            # header. Note that this grabs the activity lock, so we don't want to do it
            # here.
            if debug:
                print("Getting camera temperature information.")
            self.get_status()
            
            # Get the image from the buffer and save it to a file.
            if debug:
                print("Saving image.")            
            with self._activity_lock:
                data = self._get_image_data(checksum=checksum, debug=debug)
                self._save_data(data, filename=self._next_filename)
            
            # The file has been saved, so update the stored information.
            self._latest_image = self._next_filename
            if self._automatic_filename:
                self._latest_image_number = sequence_number
            self._image_stack.append(self._next_filename)
            self._next_filename = None
            self._is_exposing = False
            self._state['is_exposing'] = False
            return DLAPICameraResponse(success=True,description=f"Exposure completed. Image saved: {self._latest_image}")
        except:
            self._is_exposing = False
            self._state['is_exposing'] = False
            return DLAPICameraResponse(success=False,description="Error. Could not expose camera.")


    def check_exposure(self, checksum=True, debug=False):
        """Check if an asynchronous exposure is completed. If so, save image to disk.

        Args:
            checksum (bool, optional): Output MD5 checksum of image portion to log. Defaults to True.
            debug (bool, optional): Print additional help information. Defaults to False.

        Returns:
            result (str): String indicating the outcome. Possible values are:
                "No exposure has been started."
                "Exposure in progress. Time remaining: [INTEGER] seconds."
                "Exposure completed. Image saved: [FILENAME]"
                
        Notes:
            Use this function is paired with expose(wait=False) to obtain data from 
            an asynchronous expsoure. 
        """
        
        # Check if an exposure is in progress. If not, bail out.
        if self._state['is_exposing'] == False:
            return "No exposure has been started."
        
        # Check if the exposure could conceivably be completed.
        if (datetime.now() - self._exposure_start_datetime) < timedelta(seconds=self._exposure_duration):
            return f"Exposure in progress. Time remaining: {self.exposure_time_remaining()} seconds."
        
        # Time's up! But we might need to wait a little longer, as the camera
        # might need to move the image into the buffer. So wait for that to
        # finish.
        try:
            with self._activity_lock:
                self._wait_for_exposure_to_complete()
        except DLAPICameraError:
            self.logger.error("Attempting to get image data anyway.")
            pass
        
        # Get the status of the camera so the correct temperature information
        # gets written to the header. Note that this method grabs the activity
        # lock, so we don't want to do it here.
        self.get_status()
        
        # Get the image from the buffer and save it to a file.
        with self._activity_lock:
            data = self._get_image_data(checksum=checksum, debug=debug)
            self._save_data(data, filename=self._next_filename)
        
        # Update the stored information.
        self._latest_image = self._next_filename
        self._image_stack.append(self._next_filename)
        if self._automatic_filename:
            self._latest_image_number = self._latest_image_number + 1
        self._next_filename = None
        self._is_exposing = False
        self._state['is_exposing'] = False
        return DLAPICameraResponse(success=True,description=f"Exposure completed. Image saved: {self._latest_image}")
        
        
    def get_status(self):
        """Get general status of the camera.

        Returns:
            state (dict): General status of the camera.
        """
        if not self._state['is_connected']:
            return DLAPICameraResponse(success=False,description="Error. Camera not connected.")
        with self._activity_lock:
            handlePromise(self.camera.queryStatus())
        if self._state['supports_cooling']:
            cooler = self.camera.getTEC()
            self._state['cooling_enabled'] = cooler.getEnabled()
            self._state['setpoint_temperature_c'] = round(cooler.getSetpoint(), 3)
            self._state['heatsink_temperature_c'] = round(cooler.getHeatSinkThermopileTemperature(), 3)
            self._state['sensor_temperature_c'] = round(cooler.getSensorThermopileTemperature(), 3)
            self._state['power_draw_percent'] = round(cooler.getCoolerPower(), 3)
        else:
            self._state['cooling_enabled'] = False
            self._state['setpoint_temperature_c'] = None
            self._state['heatsink_temperature_c'] = None
            self._state['sensor_temperature_c'] = None
            self._state['power_draw_percent'] = None
        self.logger.info(f"Camera status: {self._state}")
        return DLAPICameraResponse(success=True,payload=self._state,description='camera status') 
    

    def set_directory(self, dirname:str):
        """Sets the save directory.

        Args:
            dirname (string): Directory to save images in.
        """
        self.dirname = dirname
        made = False
        if not os.path.exists(self.dirname):
            made = True
            os.mkdir(self.dirname)
        highnum = highest_fits_sequence_number(self.serial_number, self.dirname)
        if highnum is None:
            highnum = 0
        self._latest_image_number = highnum
        if made:
            return DLAPICameraResponse(success=True,description=f"Camera save directory set to {self.dirname}",warnings=["DIR did NOT exist and was created."])
        else:
            return DLAPICameraResponse(success=True,description=f"Camera save directory set to {self.dirname}")
        
        
    def set_verbose(self, verbose:bool):
        """Sets whether or not to print verbose output.

        Args:
            verbose (bool): True or False.
        """
        self.verbose = verbose

    def abort_exposure(self):
        """Aborts the current exposure.
        """
        if not self._state['is_connected']:
            return DLAPICameraResponse(success=False,description="Error. Camera not connected.")
        with self._activity_lock:
            handlePromise(self.sensor.abortExposure())
        time.sleep(0.5) # It is recommended to wait a little while before doing anything else.
        self._is_exposing = False
        self._state['is_exposing'] = False
        return DLAPICameraResponse(success=True,description="Exposure aborted.")

    def exposure_time_remaining(self):
        """Returns the estimated time until the current exposure is complete.

        Returns:
            float: time in seconds until exposure is complete.
        """
        if self._state['is_exposing'] == False:
            return DLAPICameraResponse(success=True,description="Already Not Exposing.")
        else:
            time_remaining = (self._exposure_duration - (datetime.now() - self._exposure_start_datetime).seconds)
            return DLAPICameraResponse(success=True,payload={'time_remaining':time_remaining})

        
    def start_polling(self):
        """Starts polling the get_status() method every 30 seconds."""
        if not self._polling_enabled:
            self._polling_enabled = True
            self._stop_polling.clear()
            self._polling_thread = threading.Thread(target=self._poll_refresh_status, daemon=True)
            self._polling_thread.start()
            self.logger.info("Polling started.")
            return DLAPICameraResponse(success=True,description='Polling Started.')


    def stop_polling(self):
        """Stops polling the get_status() method."""
        if self._polling_enabled:
            self._stop_polling.set()
            self._polling_thread.join()
            self._polling_enabled = False
            self.logger.info("Polling stopped.")
            return DLAPICameraResponse(success=True,description='Polling Stopped.')

    ####################### HELPER METHODS #####################
    
    # IMPORTANT: None of these methods should grab the activity lock. That job will be
    # done by the methods that call these helper methods.
    
    def _start_exposure(self, exptime, open_shutter = True, readout_mode=0, 
                        use_preflash = False, use_external_trigger = False):
        if not self._state['is_connected']:
            return DLAPICameraResponse(success=False,description="Error. Camera not connected.")
        try:
            duration = exptime
            binX = self._bin_x
            binY = self._bin_y
            readoutMode = readout_mode
            isLightFrame = open_shutter
            useRBIPreflash = use_preflash
            useExtTrigger = use_external_trigger
            options = dl.TExposureOptions(duration, binX, binY, readoutMode, 
                                        isLightFrame, useRBIPreflash, useExtTrigger)
            self._exposure_duration = duration
            start = datetime.now()
            self._exposure_start_datetime = start
            self._exposure_start_time = start.isoformat('T','seconds')
            mid = start + timedelta(seconds=exptime/2.0)
            self._exposure_mid_time = mid.isoformat('T','seconds')
            end = start + timedelta(seconds=exptime)
            self._exposure_end_time = end.isoformat('T','seconds')
            handlePromise(self.sensor.startExposure(options))
        except:
            return DLAPICameraResponse(success=False,description="Error. Could not start exposure.")


    def _wait_for_exposure_to_complete(self, debug=False):
        if not self._state['is_connected']:
            return DLAPICameraResponse(success=False,description="Error. Camera not connected.")
        start = datetime.now()
        while True:
            if (datetime.now() - start).seconds > (self._exposure_duration + 5):
                self.logger.info("Error. Exposure timed out.")
                raise DLAPICameraError("Error. Exposure timed out.")
            handlePromise(self.camera.queryStatus())
            status = self.camera.getStatus()
            if status.mainSensorState ==  dl.ISensor.ReadyToDownload:
                if debug:
                    print("Data is ready to download.")
                break
            if debug:
                print("Waiting for exposure to complete...")
            time.sleep(0.5)

    
    # This is only needed because very rarely (about 1 in 5000 times)
    # the camera will not start downloading, and even though 
    # hadlePromise() is supposed to have a 10s timeout, it doesn't
    # seem to always work. So we use a thread to start the download, and
    # implement a timeout that way.
    def _start_download_with_timeout(self, timeout=10):
        event = threading.Event()
        def download_thread():
            event.set() # This signals that the thread has started.
            handlePromise(self.sensor.startDownload())
        thread = threading.Thread(target=download_thread)
        event.clear()
        thread.start()
        event.wait(timeout)
        if not event.is_set():
            raise RuntimeError("Error. Could not start download.")    


    def _get_image_data(self, checksum = False, debug = False):
        if not self._state['is_connected']:
            return DLAPICameraResponse(success=False,description="Error. Camera not connected.")
        if debug:
            print("Starting download.")
        n_max_download_attempts = 3
        n_download_attempts = 0
        while True:
            try:
                self._start_download_with_timeout(timeout=10)
                # handlePromise(self.sensor.startDownload())
                break
            except RuntimeError:
                n_download_attempts += 1
                if n_download_attempts < n_max_download_attempts:
                    self.logger.error("Could not start download. Trying again.")
                    time.sleep(1)
                    pass
                else:
                    self.logger.error("Giving up after {} attempts to download buffer.".format(n_max_download_attempts))
                    raise DLAPICameraError("Error. Could not start download.")
        
        # Turn the buffer into a 1D array of unsigned shorts
        if debug:
            print("Getting image data.")
        pImg = self.sensor.getImage()
        rawdata = pImg.getBufferData()
        n_data = pImg.getBufferLength()
        if debug:
            print(f"Buffer length: {n_data}")
        d = cppyy.ll.cast['ushort*'](rawdata)
        d.reshape((n_data,))

        # Turn the 1D list into a 2D numpy array.
        data = np.reshape(np.array(d), (self._height, self._width))
        if checksum:
            self._checksum = hashlib.md5(data).hexdigest()
            self.logger.info(f"Image bytes checksum: {self._checksum}")
        return data     


    def _save_data(self, data, filename='/tmp/tmp.fits'):
        # TODO: Keywords we still need to add:
        # TARGET, EGAIN, FOCUS, FILTER, TILT, RA, DEC, EQUINOX
        hdul = fits.HDUList()
        hdul.append(fits.PrimaryHDU())
        hdul[0].data = data
        hdul[0].header['BITPIX'] = 16
        hdul[0].header['NAXIS'] = 2
        hdul[0].header['NAXIS1'] = self._height
        hdul[0].header['NAXIS2'] = self._width
        hdul[0].header['EXPTIME'] = self._exposure_duration
        hdul[0].header['IMAGETYP'] = self._imtype
        hdul[0].header['XBINNING'] = self._bin_x
        hdul[0].header['YBINNING'] = self._bin_y
        hdul[0].header['DATE'] = self._exposure_start_time
        hdul[0].header['DATE-OBS'] = self._exposure_start_time
        hdul[0].header['DATE-MID'] = self._exposure_mid_time
        hdul[0].header['DATE-END'] = self._exposure_end_time
        hdul[0].header['CCD-TEMP'] = self._state['sensor_temperature_c']
        hdul[0].header['HSINKT'] = self._state['heatsink_temperature_c']
        hdul[0].header['SERIALNO'] = self.serial_number
        hdul.writeto(filename, overwrite=True)
        self.logger.info(f"Saved: {filename}")
        

    def _signal_handler(self, sig, frame):
        """Signal handler for SIGINT signal."""
        self.stop_polling()  # This also shuts down the polling thread.
        sys.exit(0)


    def _poll_refresh_status(self):
        """Function that is executed periodically in a thread to poll the camera information."""
        while not self._stop_polling.is_set():
            self.get_status()
            time.sleep(self._polling_interval)
            if self._stop_polling.is_set():
                break           

    
####################### HELPER GLOBAL FUNCTIONS #####################
        
def handlePromise(pPromise):
    result = pPromise.wait()
    if result != dl.IPromise.Complete:
        buf = ctypes.create_string_buffer(512)
        blng = ctypes.c_ulong(512)
        pPromise.getLastError(buf, blng)
        pPromise.release()
        raise RuntimeError(buf.value)
    pPromise.release()
    
    
def highest_fits_sequence_number(serno:str, directory:str) -> str:
    fileno_max = None
    for filename in os.listdir(directory):
        try:
            basename, ext = os.path.splitext(filename)        
            if '.fits' in ext:
                fileno = int(re.search(r'' + serno +'_(\d+)_',basename).group(1))
                if fileno_max is None or fileno > fileno_max:
                    fileno_max = fileno
        except AttributeError:
            pass    
    return(fileno_max)

if __name__ == '__main__':
    print("test")