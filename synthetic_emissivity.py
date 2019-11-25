import numpy as np
import scipy.interpolate

def synthetic_emission(File='input_data/std_h_be_w_low_ne_ar_matrix.dat'):
    # define the dimensions of the grid, have to be the same as the emissivity map, see the data file
    Rcoo = np.linspace(4.04844, 8.39375, num=207)
    Zcoo = np.linspace(-4.52320, 4.67211, num=429)
    thetacoo = np.linspace(0, np.pi * 2, 1)

    xxx = [map(float, ln.split()) for ln in open(File) if ln.strip()]
    yyy = np.array(xxx)
    zzz = []
    # change the shape of the matrix
    for i in range(0, yyy.shape[0]):
        y = list(yyy[i])
        for j in range(0, len(y)):
            zzz.append(y[j])
    ValRTZ = np.array(zzz)
    ValRTZ = ValRTZ.reshape(len(Zcoo), len(Rcoo))

    # Get the interpolation from scipy
    out = scipy.interpolate.RectBivariateSpline(Rcoo, Zcoo, ValRTZ.T, kx=1, ky=1, s=0)

    # Compute the interpolation function
    def Emiss_interp(PtsXYZ, out=out, t=None):
        R = np.hypot(PtsXYZ[0, :], PtsXYZ[1, :])
        result=np.zeros((1, PtsXYZ.shape[1]))
        result[0,:]=out(R, PtsXYZ[2, :], grid=False)
        return result

    return Emiss_interp

# the emissivity with which we want to compute
ff = synthetic_emission()