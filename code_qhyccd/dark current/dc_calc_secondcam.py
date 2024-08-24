import os
import numpy as np
import matplotlib.pyplot as plt
from astropy.stats import sigma_clip
from astropy.io import fits

class DarkCurrentCalculator:
    def __init__(self, root_dir, bias_filename='master_bias.fits', figure_name='dark_current_plot'):
        self.root_dir = root_dir
        self.bias_path = os.path.join(root_dir, bias_filename)
        self.plot_path = os.path.join(root_dir, f'{figure_name}.png')

    def load_master_bias(self):
        with fits.open(self.bias_path) as hdul:
            master_bias = hdul[0].data
        return master_bias

    def load_fits_images(self, directory):
        images = []
        for filename in os.listdir(directory):
            if filename.endswith('.fits'):
                with fits.open(os.path.join(directory, filename)) as hdul:
                    images.append(hdul[0].data)
        return np.array(images)

    def create_time_dict(self, exp_times):
        data = {}
        for time in exp_times:
            data_path = os.path.join(self.root_dir, f'dark_frames_exp_{time}s')
            dark_frames = self.load_fits_images(data_path)
            avg_dark_frame = np.mean(dark_frames, axis=0)
            data[time] = avg_dark_frame
        return data

    def subtract_master_bias(self, data, master_bias):
        for key, frame in data.items():
            print(f"Min: {np.min(frame)}")
            print(f"Max: {np.max(frame)}")
            print(f"Mean: {np.mean(frame)}")
            subFrames = frame - master_bias
            subFrames = np.mean(subFrames)
            data[key] = subFrames
        return data

    def clip_frames(self, data):
        for key, frameList in data.items():
            maskedFrame = sigma_clip(frameList, sigma=3, maxiters=None)
            fillValue = np.ma.mean(maskedFrame)
            maskedFrame = maskedFrame.filled(fillValue)
            data[key] = maskedFrame
        return data

    def calculate_dark_current(self, exp_times):
        master_bias = self.load_master_bias()
        dark_data = self.create_time_dict(exp_times)
        dark_data = self.clip_frames(dark_data)
        dark_data = self.subtract_master_bias(dark_data, master_bias)

        return dark_data

    def graph_dc_vs_time(self, dark_data, exp_times):
        times = np.array(exp_times)
        values = np.array([np.mean(dark_data[time]) for time in exp_times])

        plt.figure()
        plt.plot(times, values, marker='.', linestyle='-', label='Dark Current')
        # Calculate the rise-over-run (slope)
        rise = values[-1] - values[0]
        run = times[-1] - times[0]
        slope = rise / run
        # Plot the line
        plt.plot(times, values, label=f'(DC: {slope:.4f})')
        
        plt.xlabel('Exposure Time (s)')
        plt.ylabel('Mean Dark Current (ADU)')
        plt.title('Dark Current vs Exposure Time')
        plt.legend()
        plt.grid(True)
        plt.savefig(self.plot_path)
        plt.show()

        print(f'Dark Current Slope: {slope:.4f} ADU/s')
        return slope

if __name__ == '__main__':
    root_dir = r'C:\Users\ishas\Downloads\output'
    exp_times = [1, 10, 60, 120, 240]
    dc_calculator = DarkCurrentCalculator(root_dir)
    dark_data = dc_calculator.calculate_dark_current(exp_times)
    dc_calculator.graph_dc_vs_time(dark_data, exp_times)
