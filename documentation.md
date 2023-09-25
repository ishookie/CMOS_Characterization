# fitsLoader Documentation

The `fitsLoader` class is designed to facilitate the loading and manipulation of FITS (Flexible Image Transport System) files within a specified directory. This class provides methods for loading FITS images, extracting header information, and retrieving specific header values.

## Class: fitsLoader

### Constructor: `__init__(self, folderPath)`

#### Description
This constructor initializes an instance of the `fitsLoader` class with the provided `folderPath` parameter, which should be the path to the directory containing FITS image files. It also initializes an empty list called `images` to store the loaded FITS image data.

#### Parameters
- `folderPath` (str): The path to the directory containing FITS image files.

### Method: `loadImages(self)`

#### Description
This method loads FITS images from the directory specified during object initialization (`folderPath`) and appends the image data (primary header) to the `images` list.

#### Usage
```python
fits_loader = fitsLoader('/path/to/folder')
fits_loader.loadImages()

# RON Class Documentation

The `RON` class provides functionalities for calculating the Read-Out Noise (RON) of pixel values from a set of FITS images, performing sigma clipping, and visualizing statistics using matplotlib.

## Class: RON

### Class Attribute: `threshold`

- Sigma Threshold for sigma clipping. By default, it is set to 3.

### Constructor: `__init__(self, relativePath)`

#### Description
The constructor initializes an instance of the `RON` class. It takes a `relativePath` parameter, which is the path to the directory containing FITS images relative to the current script file. It loads the images using `loadImage.fitsLoader` from the specified directory.

#### Parameters
- `relativePath` (str): The relative path to the directory containing FITS images.

#### Usage
```python
ron_calculator = RON('relative/path/to/images')

