# Characterizing sCMOS sensors
This repository contains code to help characterize and identify noise and other secondary effects that impact sCMOS sensors particuarly for use in astronomy.
  1. [CCD vs CMOS](#ccd-vs-cmos)
  2. [Readout Noise](#readout-noise-ron)
  3. [Dark Current](#dark-current)
  4. [Gain](#gain) 

## CCD vs CMOS 
CCD (Charge-Coupled Device) has been the most prevalent imaging sensor type for use in astronomy. In recent years CMOS (Complementary Metal-Oxide-Semiconductor) has dominated the consumer market. As a result CCD sensors are more expensive, harder to find and have less support than their CMOS counterparts. This section details how each sensor works as well as their differences in respect to use in astronomy. 

### CCD Background 
CCD sensors consist of an array of pixels. These pixels are light sensitive elements usually made of silicon. When photons strike these pixels electrons are released. These electrons are transfered through the sensor. Where they are amplified to maintain signal integrety as well as reducing [readout noise](#readout-noise-ron). These electrons are then converted to a descrete signal using a single ADC (analog to digital converter) which converts the electrons coming from each pixel to a digital value. 

### CMOS Background 
CMOS sensors are different in that the instead of a single readout circuit and ADC that reads values from all of the pixels, each pixel has its own readout circitry as well as each row of pixels has its own ADC. This allows for a much faster framerate and more effecient readout process. This is extremely desirable for consumer products like iPhone cameras but for scientific applications poses some issues: 
  1. Readout circuitry on the pixels themselves make it so the sensor has a smaller area exposed to light and a lower sensitivity.
  2. More ADC's provide additional and varied readout noise which cannot be compensated as easily as a CCD sensor.
  3. Noise properties are varied from pixel to pixel which makes characterizing and removing noise a more complex issue. 

![ccd vs cmos diagram](https://www.testandmeasurementtips.com/wp-content/uploads/2019/05/ccd-cmos-image-sensors.jpg) 

## Readout Noise RON
Located in RON_CMOS directory. 

This is the noise introduced through the readout circitry, mainly the preamplifier and ADC. Usually measured in e- RMS. Follows a skewed histogram distribution as opposed to CCD sensors which a follow a guassian one.

### Procedure 
1. Take N bias frames (0s exposure shutter closed) 
2. For every pixel of coordinate (x,y) calculate: $\sigma$ between the N frames
3. Repeat for every pixel in the frame. This results in an array containing the RON of each pixel
4. Remove "hot" pixels by performing 3-sigma-clipping on the RON array. 

### Analysis 
Currently I have not been able to get a reasonable number for the gain so to convert the RON noise figures from ADU to e- I will be using the stock gain value taken from diffraction's website which is **1.2 e-/ADU** on the high gain mode. 

For N = 100 I got the following results: 

**-5.0C (High Gain Mode)**
- Min Value: 0.908 ADU
- Max Value: 2.448 ADU
- **Mean Value: 1.490 ADU**

RON = 1.490 ADU * 1.2 e-/ADU = **1.778 e-**

$\text{Percent Error} = \frac{1.788-1.9}{1.9} = \text{5.895 Percent}$

The bottleneck of this calucation is the size of memory. During the subtraction the result is a numpy 3D array of size n x 2208 x 3216. With a array of 64 bit floats. The computer I am using has 32 GB RAM -> assuming 31GB usage the most images I can compile is 545. 

Running the calculation for **545 Frames at -10.0C** I get the following results:
- Min: 1.194192382537768
- Max: 2.5905072964950713
- **Mean: 1.497172421554032**

![ron-545Frames](https://github.com/aidanmacnichol/CMOS_Characterization/assets/108359181/74564315-9889-4f66-bb0b-4374178d7279)

In order to fit more images into memory a possible solution is to type the data as a 32 bit float. This would result in loss of precision. 
Running the calculation for the same **545 frames at -10.0C** I get the following results:
- Min: 1.194192886352539
- Max: 2.590508460998535
- **Mean: 1.4971725940704346**

![545-float32RON](https://github.com/aidanmacnichol/CMOS_Characterization/assets/108359181/1ba7eb21-4778-4ab4-b7e6-8e2814d15e80)

### Notes to Myself
Pixel data is stored as an uint16 ($2^{16} = 65,536$ total values) an issue arrives when I want to subtract bias frames from eachother to get a master bias. I end up getting a negative value for some pixels which results in wrap around overflow and blows up the stdev of the frame. 
  - need to look into **BSCALE** and **BZERO** which I believe is automatic scaling for fits images and may be the issue of this problem?
  - could also need to introduce an offset before I do the subtractions. How would I choose the offset? would it just be 65,536 to account for a worse case scenario? but then more overflow would occur and I would need to account for that with an array that has uint32.

    
## Dark Current
Dark current is the charge buildup on the sensor as a result of heat. This process is light independent noise. For example a specification of 0.5 e-/p/s means every 1 e-/pixel generated per 2 seconds exposure time. This can be reduced through cooling. 
There are three main sources of dark current: 
  1. Diffusion
  2. Thermal generation due to recombination (G-R) of charges
  3. Leakage currents

### Procedure
1. Take N dark frames at multiple different exposure times, same temperature
2. Average N frames and subtract a master bias from them
3. Graph Dark Current Count vs Time. Slope is the dark current
4. 
### Analysis 
10 frames were taken at each exposure time: 1s, 10s, 60s, 120s and 240s and the following graph was obtained:

![DCvsTimeAdjusted](https://github.com/aidanmacnichol/CMOS_Characterization/assets/108359181/cf8eb523-6e39-4065-8e16-84db7437395f)

The resulting DC value is 0.17 e-/p/s

The sensor used clearly has areas more succeptable to dark current than others. A exagerated image showing this spots is shown below: 

![image](https://github.com/aidanmacnichol/CMOS_Characterization/assets/108359181/5886d752-cd93-4dfb-9813-12ff304b60e6)

## Gain 
Gain is the conversion between from arbitrary ADU units to electrons. i.e a gain of 6e-/ADU means there are six electrons per ADU. 

### Procedure 
1. Take N flats at the same exposure time but varying luminance
2. Take N darks at the same exposure time
3. Create Master Dark by taking the mean between N frames
4. For each flat subtract the master dark, then calculate the mean and variance of a qxq area of the image where it is "flattest" (avoid edges due to weird edge effects)
5. Plot Variance vs Mean and calculate the slope, this is the gain. 

### Analysis 
I took a series of flat images all at -5.0C. The exposure time was at 0.2 seconds. My lightsource was my laptop screen with a white image fullscreened. I increased the brightness for each photo and took 6 in total. 

The resulting photon transfer curve (PTC) for the central 300x300 region is shown below: 

![Photon Transfer Curve  Center 300x300](https://github.com/aidanmacnichol/CMOS_Characterization/assets/108359181/c8048731-f0a1-434a-9176-e98bd1ae119b

From the slope we can see that the gain is 0.83 e-/ADU


### Notes
flat frames where pretty good actually (Here is a 2s one): 
![image](https://github.com/aidanmacnichol/CMOS_Characterization/assets/108359181/5e7d49ac-1cf8-47df-a022-8ec6b1ea1080)



# Setup
I am using the SBIG STC-428 sCMOS camera from Difraction limited. 

Connect the camera to power, the computer and then plug in the cable from the filter wheel into the "Aux" port. 

Open MaximDL and select the "Toggle Camera Control" icon in the toolbar. Go to the "Setup" tab and under "Camera 1" select "Setup Camera" then in the new window select "Advanced..." select the camera from the Device list on the left should be something like "STC428M-20092901 [USB]" Then hit Ok. 

Then hit the "Setup Filter" option under "Camera 1" select **DL Imaging+FW** from the dropdown list on the right. Then hit Ok and select "Options" on "Camera 1" Make sure the "Use Filter Wheel as Shutter" box is checked. I dont believe the "Filter to use As Shutter" dropdown matters I just have Luminance selected. 

Finally hit "Connect" to set the Cooler temp hit "Cooler" under "Camera 1" 

to take a photo go to the "Expose" tab and hit start when you have selected the desired settings. 
