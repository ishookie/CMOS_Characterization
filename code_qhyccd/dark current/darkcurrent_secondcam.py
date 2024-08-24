import os
import sys
import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clip
from ctypes import *

import time  # Import the time module for sleeping

# Add the directory containing qcam to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'path_to_qcam'))

# Import the qcam module
from qcam.qCam import *

# Path to the QHYCCD DLL
sdk_path = r"C:\Program Files\QHYCCD\AllInOne\sdk\x64"
cam = Qcam(os.path.join(sdk_path, 'qhyccd.dll'))

print("Current working directory:", os.getcwd())

COOLER_ON = 1
COOLER_OFF = 2
CONTROL_COOLER = 18
CONTROL_CURTEMP = 14
CONTROL_CURPWM = 15

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

def setup_camera(cam_id, read_mode=1, target_temp=-20.0, gain=56):
    print('Opening camera %s' % cam_id.decode('utf-8'))
    cam_handle = cam.so.OpenQHYCCD(cam_id)
    if cam_handle is None:
        print('Failed to open camera %s' % cam_id)
        return None

    # Set the specified read mode
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
    cam.so.SetQHYCCDParam(cam_handle, cam.CONTROL_GAIN, c_double(gain))
    cam.so.SetQHYCCDParam(cam_handle, cam.CONTROL_OFFSET, c_double(0))

    # Check if cooler control is available
    ret = cam.so.IsQHYCCDControlAvailable(cam_handle, CONTROL_COOLER)
    if ret == cam.QHYCCD_SUCCESS:
        print("Can operate this camera temperature control.")
        ret = cam.so.SetQHYCCDParam(cam_handle, CONTROL_COOLER, c_double(target_temp))
        if ret == cam.QHYCCD_SUCCESS:
            print("Set camera temperature successfully.")
        else:
            print("Failed to set camera temperature.")
    else:
        print("Cooler control is not available for this camera.")

     # Wait until the camera reaches the target temperature
    now_temp = c_double()
    now_temp= cam.so.GetQHYCCDParam(cam_handle, CONTROL_CURTEMP)
    print(f'Current temperature: {now_temp} °C')

    return cam_handle

def capture_frames(cam_handle, cam_id, exposure_time, num_frames, frame_type, directory):
    i_w = cam.camera_params[cam_id]['image_width'].value
    i_h = cam.camera_params[cam_id]['image_height'].value

    if not os.path.exists(directory):
        os.makedirs(directory)
    
    for frame_num in range(1, num_frames + 1):
        image_width_byref = c_uint32()
        image_height_byref = c_uint32()
        bits_per_pixel_byref = c_uint32()
        channels_byref = c_uint32()
        prev_img_data = (c_uint16 * (i_w * i_h))()

        cam.so.SetQHYCCDParam(cam_handle, cam.CONTROL_EXPOSURE, c_double(exposure_time * 1000 * 1000))  # Convert seconds to microseconds
        print(f"Setting exposure time to {exposure_time * 1000 * 1000} microseconds")

        success = cam.so.SetQHYCCDResolution(cam_handle, 0, 0, i_w, i_h)
        success = cam.so.ExpQHYCCDSingleFrame(cam_handle)
        if success != cam.QHYCCD_SUCCESS:
            print(f'Exposure failed for {frame_type} frame {frame_num} with exposure time {exposure_time} s')
            continue

        success = cam.so.GetQHYCCDSingleFrame(cam_handle,
                                              byref(image_width_byref),
                                              byref(image_height_byref),
                                              byref(bits_per_pixel_byref),
                                              byref(channels_byref),
                                              prev_img_data)
        if success == cam.QHYCCD_SUCCESS:
            print(f'{frame_type.capitalize()} frame {frame_num} captured successfully with exposure time {exposure_time} s!')
            image = np.ctypeslib.as_array(prev_img_data).reshape(i_h, i_w)
            filename = os.path.join(directory, f'{frame_type}_frame_{frame_num}_exp_{exposure_time:.2f}s.fits')
            save_frame_as_fits(image, filename)
        else:
            print(f'Failed to capture {frame_type} frame {frame_num}')

def save_frame_as_fits(frame, filename):
    hdu = fits.PrimaryHDU(frame)
    hdul = fits.HDUList([hdu])
    hdul.writeto(filename, overwrite=True)
    print(f'Frame saved as FITS: {os.path.abspath(filename)}')

def create_master_bias(bias_frames):
    clipped_frames = [sigma_clip(frame, sigma=3, maxiters=None).filled(np.mean(frame)) for frame in bias_frames]
    master_bias = np.mean(clipped_frames, axis=0)
    return master_bias

def load_fits_images(directory):
    images = []
    for filename in os.listdir(directory):
        if filename.endswith('.fits'):
            with fits.open(os.path.join(directory, filename)) as hdul:
                images.append(hdul[0].data)
    return np.array(images)

def perform_dark_current_experiment(cam_id, read_mode=1, target_temp=-20.0, gain=56, exposure_times=[1, 10, 40, 60, 90, 120, 150, 240], num_frames=5):
    # Initialize and setup the camera
    cam_handle = setup_camera(cam_id, read_mode, target_temp, gain)
    if cam_handle is None:
        return

    try:
        # Capture bias frames
        print(f"Capturing {num_frames} bias frames...")
        capture_frames(cam_handle, cam_id, 0, num_frames, 'bias', 'output/bias_frames')
        
        # Load bias frames and create master bias
        bias_frames = load_fits_images('output/bias_frames')
        master_bias = create_master_bias(bias_frames)
        master_bias_filename = 'output/master_bias.fits'
        save_frame_as_fits(master_bias, master_bias_filename)
        print(f'Master bias saved as: {os.path.abspath(master_bias_filename)}')

        for exposure_time in exposure_times:
            # Capture dark frames
            print(f"Capturing {num_frames} dark frames with exposure time {exposure_time} seconds and temperature...")

            # Print current temperature to check if cooler is working
            now_temp = c_double()
            now_pwm = c_double()
            ret_temp = cam.so.GetQHYCCDParam(cam_handle, CONTROL_CURTEMP)
            ret_pwm = cam.so.GetQHYCCDParam(cam_handle, CONTROL_CURPWM)
            if ret_temp == cam.QHYCCD_SUCCESS and ret_pwm == cam.QHYCCD_SUCCESS:
                print(f'Now camera temperature is {now_temp.value:.1f} °C, PWM is {now_pwm.value / 255.0 * 100:.1f}%')
            else:
                print(f"current temperature (ret_temp: {ret_temp}), PWM (ret_pwm: {ret_pwm})")

            capture_frames(cam_handle, cam_id, exposure_time, num_frames, 'dark', f'output/dark_frames_exp_{exposure_time}s')

    finally:
        # Ensure the camera is closed even if an error occurs
        cam.so.CloseQHYCCD(cam_handle)

    return

@CFUNCTYPE(None, c_char_p)
def pnp_in(cam_id):
    print("Camera connected: %s" % cam_id.decode('utf-8'))
    init_camera_param(cam_id)
    cam.camera_params[cam_id]['connect_to_pc'] = True
    os.makedirs(cam_id.decode('utf-8'), exist_ok=True)
    perform_dark_current_experiment(cam_id, read_mode=1, target_temp=-20.0, gain=56, exposure_times=[1, 10, 60, 120, 240], num_frames=10)

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
