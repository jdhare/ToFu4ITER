# ToFu4ITER

## Installation

You need ToFu 1.4+. You can follow the insutrctions here: https://tofuproject.github.io/tofu/installation.html 
I tend to use the development version as the code is changing rapidly, and I create a new conda env for each release.
On the IPP cluster, use module load miniconda to get a lightweight conda distribution.

You also need to run:
* conda install -c conda-forge pyexcel-ods3
* conda install -c anaconda requests

You provide your login details for BSCW by creating a file called `login_details.py` in the root directory of this repo. 
Do not upload this! It should contain the following

    usr='string_with_username'
    pwd='string_with_password'
    
## Usage
Currently there are two module, `TFI_read_camera_paramters` and `synthetic_emissivity` and several scripts.

### TFI_read_camera_parameters
contains code to grab the latest Collimator Optimisation spreadsheet from BSCW (or use a local version) 
and then it generates a series of dictionaries for each camera location: Vaccuum vessel (VV), Divertor casette (DC), Port plug collimator type (PPC),
Port Plug pinhole tpe (PPP).

It then calculates the location of the detectors and collimators/pinholes for each channel and creates ToFu camera objects for each.
Currently ToFu only calculates the power using the line of sight (LoS) approximation, so we also take the precalculated etendue from 
the spreadsheet and include that, so that we can calculate the power, and not just the brightness.

### synthetic_emissivity
This module provides a function which loads data from a file, 
and then outputs a function which interpolates the emission as required by ToFu. 
At the moment we only have one [synthetic emission file](https://bscw.rzg.mpg.de/bscw/bscw.cgi/d557520/55.D1-FPA384_03_TN--Radiation-Data_IPP_10167508.pdf) - future data will probably be loaded via IMAS.

### plot_cameras_script
This plots all of the cameras onto one poloidal cross section of the ITER vessel. All cameras are placed onto that cross section, 
though they may be in different toroidal locations.
It is rarely useful to have all LoS plotted on the vessel, but this script provides the raw code to plot subsets.

### plot_emissivity
A not very good script for finding the size of the ITER VV, and then interpolate the synthetic emissivity in this area and plotting it.

##write_emissivity
A terrible file name. This file writes the power on each sensor (divided by 2 to account for the ECRH grids).
It includes the etendue, in case that's something you want to knue.
This was for a specific request, but the code is useful for other things (histograms!) so it stays.

