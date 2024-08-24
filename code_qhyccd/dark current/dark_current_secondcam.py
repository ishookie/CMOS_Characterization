import os
import sys
import numpy as np
import time
import matplotlib.pyplot as plt
from PIL import Image as PIL_image
from astropy.io import fits
from astropy.stats import sigma_clip
from scipy.ndimage import uniform_filter
from datetime import datetime
from ctypes import *

# Add the directory containing qcam to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'path_to_qcam'))

# Import the qcam module
from qcam.qCam import *

# Path to the QHYCCD DLL
sdk_path = r"C:\Program Files\QHYCCD\AllInOne\sdk\x64"
cam = Qcam(os.path.join(sdk_path, 'qhyccd.dll'))

def init_camera_param(cam_id):
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

def setup_camera(cam_id):
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

def capture_frames(cam_handle, cam_id, num_frames, exposure_time, frame_type='dark'):
    i_w = cam.camera_params[cam_id]['image_width'].value
    i_h = cam.camera_params[cam_id]['image_height'].value
    frames = []
    
    for _ in range(num_frames):
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
            continue

        success = cam.so.GetQHYCCDSingleFrame(cam_handle,
                                              byref(image_width_byref),
                                              byref(image_height_byref),
                                              byref(bits_per_pixel_byref),
                                              byref(channels_byref),
                                              prev_img_data)
        if success == cam.QHYCCD_SUCCESS:
            print('Frame captured successfully!')
            image = np.ctypeslib.as_array(prev_img_data).reshape(i_h, i_w)
            frames.append(image)
        else:
            print('Failed to capture frame', success)
    
    return frames

def create_master_bias(bias_frames):
    clipped_frames = [sigma_clip(frame, sigma=3, maxiters=None).filled(np.mean(frame)) for frame in bias_frames]
    master_bias = np.mean(clipped_frames, axis=0)
    return master_bias

def calculate_dark_current(dark_frames, master_bias, exposure_time):
    dark_current_frames = [((frame - master_bias) / exposure_time) for frame in dark_frames]
    dark_current = np.mean(dark_current_frames, axis=0)
    return dark_current

def save_fits_image(image, filename):
    hdu = fits.PrimaryHDU(image)
    hdul = fits.HDUList([hdu])
    hdul.writeto(filename, overwrite=True)
    print(f'Image saved as FITS: {filename}')

def plot_dark_current(dark_current, exposure_times, plot_name):
    """
    Plot Dark Current Count vs Time
    Also display Dark Current (slope of linear fit)
    """
    # Calculate the rise-over-run (slope)
    plt.figure()
    slopes = []
    for key in dark_current:
        times = np.array(exposure_times)
        values = np.array(dark_current[key])
        slope, intercept = np.polyfit(times, values, 1)
        slopes.append(slope)
        plt.plot(times, values, label=f'{key}C (Slope: {slope:.4f})')

    plt.xlabel('Time (s)')
    plt.ylabel('Dark Current (e-/s)')
    plt.title('Dark Current Over Time')
    plt.legend()
    plt.grid(True)
    plt.savefig(f"{plot_name}_dark_current.png")
    plt.show()

def perform_dark_current_test(cam_id, temperatures, exposure_times, num_frames=10):
    # Initialize and setup the camera
    cam_handle = setup_camera(cam_id)
    if cam_handle is None:
        return

    # Capture bias frames and create master bias for each temperature
    master_bias_dict = {}
    for temp in temperatures:
        cam.so.SetQHYCCDParam(cam_handle, cam.CONTROL_CURTEMP, c_double(temp))
        time.sleep(60)  # Wait for the temperature to stabilize
        bias_frames = capture_frames(cam_handle, cam_id, 20, 0, frame_type='bias')
        master_bias = create_master_bias(bias_frames)
        master_bias_dict[temp] = master_bias
        save_fits_image(master_bias, f'master_bias_{temp}C.fits')

    # Capture dark frames and calculate dark current for each temperature and exposure time
    dark_current_dict = {temp: [] for temp in temperatures}
    for temp in temperatures:
        cam.so.SetQHYCCDParam(cam_handle, cam.CONTROL_CURTEMP, c_double(temp))
        time.sleep(60)  # Wait for the temperature to stabilize
        for exposure_time in exposure_times:
            dark_frames = capture_frames(cam_handle, cam_id, num_frames, exposure_time, frame_type='dark')
            dark_current = calculate_dark_current(dark_frames, master_bias_dict[temp], exposure_time)
            save_fits_image(dark_current, f'dark_current_{temp}C_{exposure_time}s.fits')
            dark_current_dict[temp].append(np.mean(dark_current))

    # Plot dark current statistics
    plot_dark_current(dark_current_dict, exposure_times, 'dark_current_statistics')

    # Close the camera
    cam.so.CloseQHYCCD(cam_handle)
    return

@CFUNCTYPE(None, c_char_p)
def pnp_in(cam_id):
    print("Camera connected: %s" % cam_id.decode('utf-8'))
    init_camera_param(cam_id)
    cam.camera_params[cam_id]['connect_to_pc'] = True
    os.makedirs(cam_id.decode('utf-8'), exist_ok=True)

@CFUNCTYPE(None, c_char_p)
def pnp_out(cam_id):
    print("Camera disconnected: %s" % cam_id.decode('utf-8'))

def gui_start():
    cam.so.RegisterPnpEventIn(pnp_in)
    cam.so.RegisterPnpEventOut(pnp_out)
    print('Scanning for cameras...')
    cam.so.InitQHYCCDResource()

print("Path:", os.path.dirname(__file__))

gui_start()
print("Press 'q' to quit")
command = ""
while command != "q":
    command = input()