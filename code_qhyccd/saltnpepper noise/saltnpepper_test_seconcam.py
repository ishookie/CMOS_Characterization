import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.stats import sigma_clip
from ctypes import *

# Add the directory containing qcam to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'path_to_qcam'))

# Import the qcam module
from qcam.qCam import *

# Path to the QHYCCD DLL
sdk_path = r"C:\Program Files\QHYCCD\AllInOne\sdk\x64"
cam = Qcam(os.path.join(sdk_path, 'qhyccd.dll'))

class SaltAndPepperNoise:
    def __init__(self, roi_size=50, std_var=3, figure_name='Salt_and_Pepper_Noise'):
        self.roi_size = roi_size
        self.std_var = std_var
        self.figure_name = figure_name
        self.output_dir = os.path.join(os.path.dirname(__file__), '..', 'plots', 'salt_and_pepper_plots')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.plot_path = os.path.join(self.output_dir, f'{self.figure_name}_Plot.png')

    def take_bias_frames(self, cam_handle, cam_id, num_frames=100):
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

    def calculate_salt_and_pepper_noise(self, bias_frames):
        if not bias_frames:
            print("No bias frames captured.")
            return
        
        # Calculate the standard deviation of the first frame
        std = np.std(bias_frames[0])
        mean = np.mean(bias_frames[0])

        print(f"First frame mean: {mean}, std: {std}")

        # Identify high variance pixels
        high_std = np.where(bias_frames[0] > (mean + self.std_var * std))

        if len(high_std[0]) == 0 or len(high_std[1]) == 0:
            print("No high variance pixels found in the ROI.")
            return

        print(f"Starting x ROI: {high_std[0][0]}, Starting y ROI: {high_std[1][0]}")
        self.mid_roi(high_std)

        # Initialize lists to store pixel values and corresponding frame numbers
        pixel_values = []
        frame_numbers = []

        # Iterate through the subset of frames
        for i, frame in enumerate(bias_frames):
            # Get the ROI
            subset = frame[self.start_x:self.end_x, self.start_y:self.end_y].astype(np.int16)
            # List of frame numbers
            frame_numbers.append(i) 
            # List of lists containing pixel values
            flat_array  = subset.flatten()
            pixel_values.append(list(flat_array))

        print(f"Number of frames: {len(frame_numbers)}, Number of pixel values per frame: {len(pixel_values[0])}")
        
        # Print a sample of the pixel values
        print("Sample pixel values:", pixel_values[0][:10])

        # Flatten the list of pixel values for the y-axis
        all_pixel_values = [value for sublist in pixel_values for value in sublist]

        # Plot all pixels across frames
        for x, y in zip(frame_numbers, pixel_values):
            plt.scatter([x] * len(y), y, color='red')

        plt.ylim(min(all_pixel_values) - 10, max(all_pixel_values) + 10)
        plt.xlabel('Frame Number')
        plt.ylabel('ADU Pixel Value')
        plt.title("Salt and Pepper Noise (Random Telegraph Noise) +/-3 std")

        plt.savefig(self.plot_path)
        plt.show()

    def mid_roi(self, indexes):
        """
        Given coordinates of a high variance pixel, get the ROI region.
        """
        self.start_x = indexes[0][0]
        self.start_y = indexes[1][0]
        self.end_x = self.start_x + self.roi_size 
        self.end_y = self.start_y + self.roi_size

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

def setup_camera(cam_id, read_mode=0, target_temp=-5.0, gain=26):
    print('Opening camera %s' % cam_id.decode('utf-8'))
    cam_handle = cam.so.OpenQHYCCD(cam_id)
    if cam_handle is None:
        print('Failed to open camera %s' % cam_id)
        return None

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

    cam.so.SetQHYCCDParam(cam_handle, cam.CONTROL_EXPOSURE, c_double(0))
    cam.so.SetQHYCCDParam(cam_handle, cam.CONTROL_GAIN, c_double(gain))
    cam.so.SetQHYCCDParam(cam_handle, cam.CONTROL_OFFSET, c_double(0))

    cam.so.SetQHYCCDParam(cam_handle, cam.CONTROL_COOLER, c_double(target_temp))
    
    return cam_handle

def perform_salt_and_pepper_noise_test(cam_id, read_mode=0, target_temp=-5.0, gain=26, num_bias_frames=100):
    cam_handle = setup_camera(cam_id, read_mode, target_temp, gain)
    if cam_handle is None:
        return
    
    try:
        # Step 1: Capture bias frames
        salt_pepper_test = SaltAndPepperNoise()
        bias_frames = salt_pepper_test.take_bias_frames(cam_handle, cam_id, num_bias_frames)
        
        # Step 2: Calculate salt and pepper noise
        salt_pepper_test.calculate_salt_and_pepper_noise(bias_frames)
        
    finally:
        cam.so.CloseQHYCCD(cam_handle)

    return

@CFUNCTYPE(None, c_char_p)
def pnp_in(cam_id):
    print("Camera connected: %s" % cam_id.decode('utf-8'))
    init_camera_param(cam_id)
    cam.camera_params[cam_id]['connect_to_pc'] = True
    os.makedirs(cam_id.decode('utf-8'), exist_ok=True)
    perform_salt_and_pepper_noise_test(cam_id, read_mode=0, target_temp=-5.0, gain=26, num_bias_frames=100)

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
