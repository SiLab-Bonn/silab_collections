"""
The fit examples in this script work on a simulated, Gaussian-distributed response of a detector system
with discrete channels such as e.g. counts in a multi-channels analyzer (MCA) or a pixel detector TOT. 
"""

import numpy as np
from silab_collections.fit import fit
import matplotlib.pyplot as plt


# Generate normal distributed example data set
MU = 50
SIGMA = 1.5
N_SAMPLES = 100_000
NORMAL_SAMPLES = np.random.normal(loc=MU, scale=SIGMA, size=N_SAMPLES)  # Draw from normal distribution with given mu and sigma

# Make data for fitting
DATA, _edges = np.histogram(NORMAL_SAMPLES, bins=100)
CHANNELS = (_edges[1:] + _edges[:-1]) / 2.0


def gauss(x, mu, sigma, amplitude):
    # Define Gaussian as fit function
    return amplitude * np.exp(-0.5 * (x - mu)**2 / sigma**2)


def fit_basic_example():
    """
    Example of fit.fit_basic function

    We generate a Gaussian-distributed counts with corresponding channel numbers which would be
    a typical use-case for fit_basic because channels are discrete (a.k.a no errors are assumed)
    """
    
    # Calculate uncertainty on the data
    y_err = np.sqrt(DATA)

    # Set uncertainty to infinity where the uncertainty is 0 in order to not restrict the fit
    y_err[y_err == 0] = np.inf

    # Estimator for starting parameters for the fit routine
    p0 = [60, 2, DATA.max()]

    # Do the fit
    popt, perr, red_chi_2 = fit.fit_basic(fit_func=gauss,
                                          x=CHANNELS,
                                          y=DATA,
                                          y_err=y_err,
                                          p0=p0)

    # Make result string
    res = "Fit results of {}:\n\t".format(fit.fit_basic.__name__)
    res += "mu = ({:.3E} {} {:.3E})".format(popt[0], u'\u00B1', perr[0]) + " channel\n\t"
    res += "sigma = ({:.3E} {} {:.3E})".format(popt[1], u'\u00B1', perr[1]) + " channel\n\t"
    res += "amplitude = ({:.3E} {} {:.3E})".format(popt[2], u'\u00B1', perr[2]) + " counts\n\t"
    res += "red. Chi^2 = {:.3f}".format(red_chi_2) + "\n"
    
    # Print result str
    print(res)

def fit_odr_example():
    """
    Example of fit.fit_basic function

    We generate a Gaussian-distributed counts with corresponding channel numbers which would be
    a typical use-case for fit_basic because channels are discrete (a.k.a no errors are assumed)
    """
    
    # Calculate uncertainty on the data
    y_err = np.sqrt(DATA)

    # Set uncertainty to infinity where the uncertainty is 0 in order to not restrict the fit
    y_err[y_err == 0] = np.inf

    # Assume the channels now can be converted to energy by a calibration energy(channel) = a * channel
    # a is the calibration constant in keV / channel
    # Assume a = (1.67 +- 0.07) keV / channel with an error which is normal ditributed
    energy = 1.67 * CHANNELS

    # Now we have an error on the x fit input as well
    x_err = np.full(fill_value=0.07, shape=energy.shape)

    # Estimator for starting parameters for the fit routine
    p0 = [80, 3, DATA.max()]

    # Do the fit
    popt, perr, red_chi_2 = fit.fit_odr(fit_func=gauss,
                                        x=energy,
                                        y=DATA,
                                        x_err=x_err,
                                        y_err=y_err,
                                        p0=p0)

    # Make result string
    res = "Fit results of {}:\n\t".format(fit.fit_odr.__name__)
    res += "mu = ({:.3E} {} {:.3E})".format(popt[0], u'\u00B1', perr[0]) + " keV\n\t"
    res += "sigma = ({:.3E} {} {:.3E})".format(popt[1], u'\u00B1', perr[1]) + " KeV\n\t"
    res += "amplitude = ({:.3E} {} {:.3E})".format(popt[2], u'\u00B1', perr[2]) + " counts\n\t"
    res += "red. Chi^2 = {:.3f}".format(red_chi_2) + "\n"
    
    # Print result str
    print(res)


if __name__ == '__main__':
    fit_basic_example()
    fit_odr_example()