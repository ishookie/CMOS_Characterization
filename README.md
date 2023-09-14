# Characterizing sCMOS sensors
This repository contains code to help characterize and identify noise and other secondary effects that impact sCMOS sensors particuarly for use in astronomy. 
**Split into three main catagories:**
  1. [CCD vs CMOS](#ccd-vs-cmos)
  2. [Readout Noise](#readout-noise-(ron))
  3. [Dark Current](#dark-current)
  4. [Gain](#gain) 

## CCD vs CMOS 
CCD (Charge-Coupled Device) has been the most prevalent imaging sensor type for use in astronomy. In recent years CMOS (Complementary Metal-Oxide-Semiconductor) has dominated the consumer market. As a result CCD sensors are more expensive, harder to find and have less support than their CMOS counterparts. This section details how each sensor works as well as their differences in respect to use in astronomy. 

### CCD Background 
CCD sensors consist of an array of pixels. These pixels are light sensitive elements usually made of silicon. When photons strike these pixels electrons are released. These electrons are transfered through the sensor. Where they are amplified to maintain signal integrety as well as reducing (readout noise)[## readout-noise-(ron)). These electrons are then converted to a descrete signal using a single ADC (analog to digital converter) which converts the electrons coming from each pixel to a digital value. 

### CMOS Background 
CMOS sensors are different in that the instead of a single readout circuit and ADC that reads values from all of the pixels, each pixel has its own readout circitry as well as each row of pixels has its own ADC. This allows for a much faster framerate and more effecient readout process. This is extremely desirable for consumer products like iPhone cameras but for scientific applications poses some issues: 
  1. Readout circuitry on the pixels themselves make it so the sensor has a smaller area exposed to light and a lower sensitivity.
  2. More ADC's provide additional and varied readout noise which cannot be compensated as easily as a CCD sensor.
  3. Noise properties are varied from pixel to pixel which makes characterizing and removing noise a more complex issue. 

![ccd vs cmos diagram](https://www.testandmeasurementtips.com/wp-content/uploads/2019/05/ccd-cmos-image-sensors.jpg) 

## Readout Noise (RON)
Located in RON_CMOS directory. 

This is the noise introduced through the readout circitry, mainly the preamplifier and ADC. Usually measured in e- RMS. Follows a skewed histogram distribution as opposed to CCD sensors which a follow a guassian one.

### Procedure 
1. Take N bias frames
2. Subtract bias frames from each other **ADD SUBTRATION ALGO? MULTIPLE FRAMES? OVERFLOW?**
3. Calculate the standard deviation of the resulting image
4. Final value is given by:
   $RON = \frac{stdev}{sqrt(N)}$ 

### Notes to Myself
Pixel data is stored as an uint16 ($2^{16} = 65,536 total values$) an issue arrives when I want to subtract bias frames from eachother to get a master bias. I end up getting a negative value for some pixels which results in wrap around overflow and blows up the stdev of the frame. 
  - need to look into **BSCALE** and **BZERO** which I believe is automatic scaling for fits images and may be the issue of this problem 
  - could also need to introduce an offset before I do the subtractions. How would I choose the offset? would it just be 65,536 to account for a worse case scenario? but then more overflow would occur and I would need to account for that with an array that has uint32.
    
## Dark Current
Dark current is the charge buildup on the sensor as a result of heat. This process is light independent noise. For example a specification of 0.5 e-/p/s means every 1 e-/pixel generated per 2 seconds exposure time. This can be reduced through cooling. **and???**__ 

## Gain 
----add info here----

