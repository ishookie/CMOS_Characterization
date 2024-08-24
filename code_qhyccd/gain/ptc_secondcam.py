import os
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.stats import sigma_clip

class PhotonTransferCurve:
    def __init__(self, base_dir, roi_size=4096, figure_name='PhotonTransferCurve'):
        self.base_dir = base_dir
        self.roi_size = roi_size
        self.figure_name = figure_name
        self.output_dir = os.path.join(self.base_dir, 'plots', 'ptc_plots')
        self.plot_path = os.path.join(self.output_dir, f'{self.figure_name}_Plot.png')
        
        # Ensure the output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def load_fits_image(self, filepath):
        with fits.open(filepath) as hdul:
            image_data = hdul[0].data
        return image_data

    def load_bias_frames(self, exposure_time, bias_type='before'):
        bias_dir = os.path.join(self.base_dir, f'bias_{bias_type}')
        bias_files = [os.path.join(bias_dir, f'bias_{bias_type}_frame_{i}_exp_{exposure_time:.2f}s.fits') for i in range(1, 4)]
        
        bias_images = [self.load_fits_image(f) for f in bias_files]
        
        # Perform median 3-sigma clipping
        clipped_frames = [sigma_clip(frame, sigma=3, maxiters=None).filled(np.mean(frame)) for frame in bias_images]
        stacked_mask = np.median(clipped_frames, axis=0)
        stacked_mask = stacked_mask.astype(np.float64)
        
        return stacked_mask

    def calculate_photon_transfer_curve(self):
        exposure_dirs = sorted([d for d in os.listdir(self.base_dir) if d.startswith('illuminated_exp')])
        exposure_times = [float(d.split('_')[-1][:-1]) for d in exposure_dirs]
        
        results = []

        for exposure_time in exposure_times:
            print(f"Processing exposure time: {exposure_time:.2f} s")
            
            bias_before = self.load_bias_frames(exposure_time, 'before')
            bias_after = self.load_bias_frames(exposure_time, 'after')
            master_bias = (bias_before + bias_after) / 2

            illuminated_dir = os.path.join(self.base_dir, f'illuminated_exp_{exposure_time:.2f}s')
            illuminated_files = [os.path.join(illuminated_dir, f'illuminated_frame_{i}_exp_{exposure_time:.2f}s.fits') for i in range(1, 4)]
            illuminated_images = [self.load_fits_image(f) for f in illuminated_files]

            corrected_illuminated_images = [image - master_bias for image in illuminated_images]

            roi = corrected_illuminated_images[0].shape[0] // 2, corrected_illuminated_images[0].shape[1] // 2
            roi_start_x = roi[0] - 2048
            roi_start_y = roi[1] - 2048
            roi_end_x = roi_start_x + 4096
            roi_end_y = roi_start_y + 4096

            roi_images = [image[roi_start_x:roi_end_x, roi_start_y:roi_end_y] for image in corrected_illuminated_images]
            
            mean_signals = [np.mean(image) for image in roi_images]
            mean_signal = np.mean(mean_signals)
            std_devs = [np.std(image) for image in roi_images]
            mean_std_dev = np.mean(std_devs)

            print(f"Mean signals for exposure time {exposure_time:.2f} s: {mean_signals}")
            print(f"Mean standard deviation for exposure time {exposure_time:.2f} s: {mean_std_dev}")
            print(f"Average mean signal for exposure time {exposure_time:.2f} s: {mean_signal}")

            results.append((mean_std_dev, mean_signal))
        
        return results

    def plot_photon_transfer_curve(self, results):
        mean_std_devs, mean_signals = zip(*results)
        
        plt.figure(figsize=(10, 6))
        plt.plot(mean_std_devs, mean_signals, 'o-', label='Measured Signal')
        plt.xlabel('Mean Standard Deviation (ADU)')
        plt.ylabel('Mean Signal (ADU)')
        plt.title('Photon Transfer Curve (PTC)')
        plt.legend()
        plt.grid(True)
        plt.savefig(self.plot_path)
        plt.show()

if __name__ == "__main__":
    base_dir = r'C:\Users\ishas\Downloads\output'
    ptc_test = PhotonTransferCurve(base_dir)
    results = ptc_test.calculate_photon_transfer_curve()
    ptc_test.plot_photon_transfer_curve(results)
