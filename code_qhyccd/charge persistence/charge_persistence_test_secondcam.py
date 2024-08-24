import os
import sys
import numpy as np
import time
import matplotlib.pyplot as plt
from astropy.io import fits
import re
import logging

# Add the directory containing qcam to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'path_to_qcam'))

# Import the qcam module
from qcam.qCam import *

# Path to the QHYCCD DLL
sdk_path = r"C:\Program Files\QHYCCD\AllInOne\sdk\x64"
cam = Qcam(os.path.join(sdk_path, 'qhyccd.dll'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class CHARGEPERSISTENCE:

    def __init__(self, numBias=300, figureName='ChargePersistence_summed_test'):
        """
        Init for the charge persistence class.

        Args:
            numBias (int, optional): Number of baises to take in 1s intervals. Defaults to 300.
            figureName (str, optional): _description_. Defaults to 'ChargePersistence_datalabel2'.
        """
        self.numBias = numBias
        self.rootPath = os.path.dirname(os.path.dirname(__file__))
        self.outputDir = os.path.join(os.path.dirname(__file__), '..', 'plots', 'charge_persistence_plots')
        self.plotPath = os.path.join(self.outputDir, f'{figureName}_Plot.png')

    def init_camera_param(self, cam_id):
        if not cam.camera_params.keys().__contains__(cam_id):
            cam.camera_params[cam_id] = {'connect_to_pc': False,
                                         'connect_to_sdk': False,
                                         'EXPOSURE': c_double(1000.0 * 1000.0),
                                         'GAIN': c_double(54.0),
                                         'CONTROL_BRIGHTNESS': c_int(0),
                                         'CONTROL_GAIN': c_int(6),
                                         'CONTROL_EXPOSURE': c_int(8),
                                         'CONTROL_CURTEMP': c_int(14),
                                         'CONTROL_CURPWM': c_int(15),
                                         'CONTROL_MANULPWM': c_int(16),
                                         'CONTROL_COOLER': c_int(18),
                                         'chip_width': c_double(),
                                         'chip_height': c_double(),
                                         'image_width': c_uint32(),
                                         'image_height': c_uint32(),
                                         'pixel_width': c_double(),
                                         'pixel_height': c_double(),
                                         'bits_per_pixel': c_uint32(),
                                         'mem_len': c_ulong(),
                                         'stream_mode': c_uint8(0),
                                         'channels': c_uint32(),
                                         'read_mode_number': c_uint32(),
                                         'read_mode_index': c_uint32(),
                                         'read_mode_name': c_char('-'.encode('utf-8')),
                                         'prev_img_data': c_void_p(0),
                                         'prev_img': None,
                                         'handle': None,
                                         }

    def setup_camera(self, cam_id):
        print('Opening camera %s' % cam_id.decode('utf-8'))
        cam_handle = cam.so.OpenQHYCCD(cam_id)
        if cam_handle is None:
            print('Failed to open camera %s' % cam_id)
            return None

        # Set read mode to 0 for simplicity (adjust as needed)
        read_mode = 0
        success = cam.so.SetQHYCCDReadMode(cam_handle, read_mode)
        cam.camera_params[cam_id]['stream_mode'] = c_uint8(cam.stream_single_mode)
        success = cam.so.SetQHYCCDStreamMode(cam_handle, cam.camera_params[cam_id]['stream_mode'])
        print('Set StreamMode   =', success)
        success = cam.so.InitQHYCCD(cam_handle)
        print('Init Camera   =', success)

        success = cam.so.SetQHYCCDBitsMode(cam_handle, c_uint32(cam.bit_depth_16))

        success = cam.so.GetQHYCCDChipInfo(cam_handle,
                                           byref(cam.camera_params[cam_id]['chip_width']),
                                           byref(cam.camera_params[cam_id]['chip_height']),
                                           byref(cam.camera_params[cam_id]['image_width']),
                                           byref(cam.camera_params[cam_id]['image_height']),
                                           byref(cam.camera_params[cam_id]['pixel_width']),
                                           byref(cam.camera_params[cam_id]['pixel_height']),
                                           byref(cam.camera_params[cam_id]['bits_per_pixel']))

        print('Camera Info:', success)
        cam.camera_params[cam_id]['mem_len'] = cam.so.GetQHYCCDMemLength(cam_handle)
        i_w = cam.camera_params[cam_id]['image_width'].value
        i_h = cam.camera_params[cam_id]['image_height'].value
        print(f'Chip: {cam.camera_params[cam_id]["chip_width"].value} x {cam.camera_params[cam_id]["chip_height"].value}')
        print(f'Pixel: {cam.camera_params[cam_id]["pixel_width"].value} x {cam.camera_params[cam_id]["pixel_height"].value}')
        print(f'Image: {i_w} x {i_h}')
        print(f'Bits per pixel: {cam.camera_params[cam_id]["bits_per_pixel"].value}')
        print(f'Memory length: {cam.camera_params[cam_id]["mem_len"]}')

        # Set parameters (example values)
        cam.so.SetQHYCCDParam(cam_handle, cam.CONTROL_EXPOSURE, c_double(0))
        cam.so.SetQHYCCDParam(cam_handle, cam.CONTROL_GAIN, c_double(0))
        cam.so.SetQHYCCDParam(cam_handle, cam.CONTROL_OFFSET, c_double(0))

        return cam_handle

    def capture_frame(self, cam_handle, cam_id, exposure_time, frame_type='bias'):
        i_w = cam.camera_params[cam_id]['image_width'].value
        i_h = cam.camera_params[cam_id]['image_height'].value

        image_width_byref = c_uint32()
        image_height_byref = c_uint32()
        bits_per_pixel_byref = c_uint32()
        channels_byref = c_uint32()
        prev_img_data = (c_uint16 * (i_w * i_h))()

        success = cam.so.SetQHYCCDResolution(cam_handle, 0, 0, i_w, i_h)
        cam.so.SetQHYCCDParam(cam_handle, cam.CONTROL_EXPOSURE, c_double(exposure_time * 1e6))  # Exposure time in microseconds
        success = cam.so.ExpQHYCCDSingleFrame(cam_handle)
        if success != cam.QHYCCD_SUCCESS:
            print('Exposure failed', success)
            return None

        success = cam.so.GetQHYCCDSingleFrame(cam_handle,
                                              byref(image_width_byref),
                                              byref(image_height_byref),
                                              byref(bits_per_pixel_byref),
                                              byref(channels_byref),
                                              prev_img_data)
        if success == cam.QHYCCD_SUCCESS:
            print('Frame captured successfully!')
            image = np.ctypeslib.as_array(prev_img_data).reshape(i_h, i_w)
            return image
        else:
            print('Failed to capture frame', success)
            return None

    def takeLight(self, cam_handle, cam_id, temp, expTime, number=1, readout_mode="High Gain"): 
        """
        Take a light frame. Saved in directory: data/chargePersistence/flat/{temp}/{readout mode}

        Args:
            temp (int): Temperature for frames to be saved at.
            expTime (int): Exposure time of light frame. 
            number (int, optional): Number of light images to be taken. Defaults to 1.
            readout_mode (str, optional): Readout mode of sensor. Either "High Gain" or "Low Gain" Defaults to "High Gain".
        """
        # Create necessary directories to save images to.
        savedir = os.path.join(self.rootPath, 'data', 'chargePersistence', 'flat', f"{str(temp)}C")
        if not os.path.exists(savedir):
            os.makedirs(savedir)
            hgPath = os.path.join(savedir, "High Gain")
            lgPath = os.path.join(savedir, "Low Gain")
            os.makedirs(hgPath)
            os.makedirs(lgPath)
        else: 
            hgPath = os.path.join(savedir, "High Gain")
            lgPath = os.path.join(savedir, "Low Gain")

        # high/low gain adjust save directory 
        if readout_mode == "High Gain":
            savedir = hgPath
        elif readout_mode == "Low Gain": 
            savedir = lgPath
        else:
            print(f"Incorrect readout mode: {readout_mode}")
            return

        # Take frames
        for n in range(number): 
            image = self.capture_frame(cam_handle, cam_id, expTime, frame_type='light')
            if image is not None:
                save_path = os.path.join(savedir, f"{temp}Cflat_{expTime}s_{readout_mode}-{n}.fits")
                self.save_fits_image(image, save_path)
        logging.info("Long light exposure done. Close the shutter immediately.")

    def takeBias(self, cam_handle, cam_id, temp, number=1, readout_mode="High Gain"): 
        """
        Take a bias image.

        Args:
            temp (int): Temperature of sensor.
            number (int, optional): Number of biases to take. Defaults to 1.
            readout_mode (str, optional): Options are either 'High Gain' or 'Low Gain'. Defaults to 'High Gain'.
        """
        # Create new directory for given temperature
        savedir = os.path.join(self.rootPath, 'data', 'chargePersistence', 'bias', str(temp))
        if not os.path.exists(savedir):
            os.makedirs(savedir)
            hgPath = os.path.join(savedir, "High Gain")
            lgPath = os.path.join(savedir, "Low Gain")
            os.makedirs(hgPath)
            os.makedirs(lgPath)
        else: 
            hgPath = os.path.join(savedir, "High Gain")
            lgPath = os.path.join(savedir, "Low Gain")
        
        # high/low gain adjust save directory 
        if readout_mode == "High Gain":
            savedir = hgPath
        elif readout_mode == "Low Gain": 
            savedir = lgPath
        else:
            print(f"Incorrect readout mode: {readout_mode}")
            return

        # Take Biases
        for n in range(number):
            image = self.capture_frame(cam_handle, cam_id, 0, frame_type='bias')
            if image is not None:
                save_path = os.path.join(savedir, f"{temp}Cbias_{readout_mode}-{n}.fits")
                self.save_fits_image(image, save_path)
        logging.info(f"Completed taking {number} bias frames at {temp}°C in {readout_mode} mode.")

    def save_fits_image(self, image, filename):
        hdu = fits.PrimaryHDU(image)
        hdul = fits.HDUList([hdu])
        hdul.writeto(filename, overwrite=True)
        print(f'Image saved as FITS: {filename}')

    def takeImages(self, cam_handle, cam_id, temp=5, expTime=3):
        """
        Take a light image immediately followed by a series of biases. 
        
        Args:
            temp (int, optional): Temperature of sensor. Defaults to 5.
            expTime (int, optional): Exposure time of light image. Defaults to 3.
        """
        # Take a light image at saturation 
        self.takeLight(cam_handle, cam_id, temp, expTime)
        input("Press Enter after closing the shutter to start taking biases...") # Wait for user to close the shutter
        # Take biases 1 second in between 
        for i in range(self.numBias):
            self.takeBias(cam_handle, cam_id, temp, number=1)
            time.sleep(1) 

    def calcPersistence(self, temp=5):
        """
        Loads biases in order they are taken and calculates mean pixel values.

        Args:
            temp (int, optional): Temperature of sensor (what biases to load). Defaults to 5.
        """
        meanCounts = []
        dataPath = os.path.join(self.rootPath, 'data', 'chargePersistence', 'bias', f'{temp}', "High Gain")
        
        # Sort files before loading 
        filenames = sorted([filename for filename in os.listdir(dataPath) if filename.endswith(".fits")],
                           key=lambda x: int(re.search(r'(\d+).fits', x).group(1)))
        
        # Load bias images. Similar to loadImage.py but done here because order matters. 
        # Also mean is calculated immediately instead of returning a 2d array of each frame.
        # This is done because the pi runs out of memory if loading all images.
        for filename in filenames:
            filePath = os.path.join(dataPath, filename)
            try:
                with fits.open(filePath) as hdul:
                    data = hdul[0].data
                    meanCounts.append(np.sum(data))
            except Exception as e:
                print(f"Error reading {filePath}: {str(e)}")
 
        # fills a list up to numBias in 1 increments. Time list.
        times = [i for i in range(1, self.numBias+1)]    
        # Print first 5 values and times
        print(f"Mean Values: {meanCounts[:5]}")
        print(f"Times: {times[:5]}")
        # Plot values
        self.plotPersistence(meanCounts, times)
    
    def plotPersistence(self, meanVals, times):
        """
        Plot mean ADU vs time

        Args:
            meanVals (list): List of mean values
            times (list): List of times
        """
        plt.plot(times, meanVals, linestyle='-', label='Line Plot')
        plt.scatter(times, meanVals, color='red', marker='o', label='Data Points')
        
        plt.xlabel('Time (s)')
        plt.ylabel('Mean ADU')
        plt.title('Charge Persistence in Biases')
        plt.legend()  # Add legend to differentiate line plot and data points
        plt.savefig(self.plotPath)
        plt.show()  # Display the plot (optional)
        return

def main():
    # Initialize the charge persistence class
    cp_test = CHARGEPERSISTENCE()

    # Start the GUI and register events
    cam.so.RegisterPnpEventIn(cp_test.pnp_in)
    cam.so.RegisterPnpEventOut(cp_test.pnp_out)
    print('Scanning for cameras...')
    cam.so.InitQHYCCDResource()

    print("Press 'q' to quit")
    command = ""
    while command != "q":
        command = input()

if __name__ == "__main__":
    main()

