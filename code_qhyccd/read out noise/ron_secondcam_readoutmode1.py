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

COOLER_ON = 1
COOLER_OFF = 2
CONTROL_COOLER = 18
CONTROL_CURTEMP = 14
CONTROL_CURPWM = 15

# Add the directory containing qcam to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'path_to_qcam'))

# Import the qcam module
from qcam.qCam import *

# Path to the QHYCCD DLL
sdk_path = r"C:\Program Files\QHYCCD\AllInOne\sdk\x64"
cam = Qcam(os.path.join(sdk_path, 'qhyccd.dll'))

print("Current working directory:", os.getcwd())

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

def setup_camera(cam_id, read_mode=0, target_temp=-10.0, gain=0):
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

    # Set the target temperature
    cam.so.SetQHYCCDParam(cam_handle, cam.CONTROL_COOLER, c_double(target_temp))
    
    return cam_handle

def capture_bias_frames(cam_handle, cam_id, num_frames):
    i_w = cam.camera_params[cam_id]['image_width'].value
    i_h = cam.camera_params[cam_id]['image_height'].value
    bias_frames = []
    
    for _ in range(num_frames):
        image_width_byref = c_uint32()
        image_height_byref = c_uint32()
        bits_per_pixel_byref = c_uint32()
        channels_byref = c_uint32()
        prev_img_data = (c_uint16 * (i_w * i_h))()

        success = cam.so.SetQHYCCDResolution(cam_handle, 0, 0, i_w, i_h)
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
            bias_frames.append(image)
        else:
            print('Failed to capture frame', success)
    
    return bias_frames

def create_master_bias(bias_frames):
    clipped_frames = [sigma_clip(frame, sigma=3, maxiters=None).filled(np.mean(frame)) for frame in bias_frames]
    master_bias = np.mean(clipped_frames, axis=0)
    return master_bias

def mean_and_variance(data, axis=0):
    """
    Calculate the mean and variance along the specified axis in a memory-efficient way.
    """
    n = data.shape[axis]
    
    # Compute mean
    mean = np.sum(data, axis=axis) / n
    
    # Compute variance
    variance = np.sum((data - np.expand_dims(mean, axis)) ** 2, axis=axis) / n
    
    return mean, variance

def calculate_ron_with_memmap(bias_frames, master_bias, shape, dtype):
    # Use memory-mapped files for large arrays
    master_bias = master_bias.astype(np.float32)  # Ensure using float32 to reduce memory usage
    ron_frames = np.memmap('ron_frames.dat', dtype=dtype, mode='w+', shape=(len(bias_frames), *shape))
    
    for i, frame in enumerate(bias_frames):
        ron_frames[i] = frame.astype(np.float32) - master_bias

    mean, variance = mean_and_variance(ron_frames, axis=0)
    ron = np.sqrt(variance / 2)  # RON calculation
    return ron

def save_fits_image(image, filename):
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    hdu = fits.PrimaryHDU(image)
    hdul = fits.HDUList([hdu])
    hdul.writeto(filename, overwrite=True)
    print(f'Image saved as FITS: {os.path.abspath(filename)}')

def plot_statistics(ron, plot_name, binning=1):
    """
    Prints: Min, Max and Mean values.
    Creates a histogram of RMS pixel values vs log(count)
    Creates a heatmap of RON absolute values.
    Args:
        data (np array): Array of pixel values representing the readout noise
        plotName (str): Name to prefix plot file names with.
        binning (int): square binning size for heatmap. Defaults to 1
    """
    # Print various statistics
    print(f"Min Value: {np.min(ron)}")
    print(f"Max Value: {np.max(ron)}")
    print(f"Mean Value: {np.mean(ron)}")

    # Create Histogram
    ron_flat = ron.flatten()
    plt.hist(ron_flat, bins=100)
    plt.title('RON Histogram')
    plt.xlabel('RON Values (ADU)')
    plt.ylabel('log(count)')
    plt.yscale('log')
    plt.savefig(f"{plot_name}_histogram.png")

    # Create a heatmap
    ron_binned = uniform_filter(ron, size=binning, mode='constant')[::binning, ::binning]
    plt.figure()  # Create a new figure for the heatmap
    heatmap = plt.imshow(ron_binned, cmap='magma', interpolation='nearest')
    plt.colorbar(heatmap)
    plt.savefig(f"{plot_name}_heatmap.png")
    plt.show()

def perform_readout_noise_test(cam_id, read_mode=0, target_temp=-10.0, gain=0, num_bias_frames=100, num_additional_frames=100):
    # Initialize and setup the camera
    cam_handle = setup_camera(cam_id, read_mode, target_temp, gain)
    if cam_handle is None:
        return
    
    try:
        # Step 1: Capture initial bias frames
        bias_frames = capture_bias_frames(cam_handle, cam_id, num_bias_frames)
        
        # Step 2: Create master bias
        master_bias = create_master_bias(bias_frames)
        master_bias_filename = 'output/master_bias.fits'
        save_fits_image(master_bias, master_bias_filename)
        print(f'Master bias saved as: {os.path.abspath(master_bias_filename)}')
        
        # Step 3: Capture additional bias frames
        del bias_frames  # Free up memory by deleting the initial bias frames
        additional_bias_frames = capture_bias_frames(cam_handle, cam_id, num_additional_frames)
        
        # Step 4: Calculate readout noise with memory mapping
        shape = (cam.camera_params[cam_id]['image_height'].value, cam.camera_params[cam_id]['image_width'].value)
        ron = calculate_ron_with_memmap(additional_bias_frames, master_bias, shape, np.float32)
        readout_noise_filename = 'output/readout_noise.fits'
        save_fits_image(ron, readout_noise_filename)
        print(f'Readout noise saved as: {os.path.abspath(readout_noise_filename)}')
        
        # Step 5: Plot statistics
        plot_statistics(ron, 'output/readout_noise_statistics')

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
    perform_readout_noise_test(cam_id, read_mode=0, target_temp=-10.0, gain=0, num_bias_frames=100, num_additional_frames=100)

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
