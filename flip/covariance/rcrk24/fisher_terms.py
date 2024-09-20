import numpy as np
from astropy.cosmology import FlatLambdaCDM

from flip.covariance.rcrk24.coefficients import (
    dOmdOm0,
    f,
    dfdOm0,
    dfdgamma,
    ds8dgamma_approx,
    ds8dO0_approx,
    s8_approx,
    cosmo_background,
)

# The flip convention is to split the power spectrum into several terms
# where linearity assumptions are made
# P_ab = AA * BB * P0_xy
#
# A is the coefficients where
# P_ab = AA P_xy
# B is the cofficient where
# P_xy = BB P0_xy
# and
# P0_xy is the power spectrum for a fiducial cosmology at z=0

# The derivative cofficients we need are
# dA/dp B + A dB/dp

# for vv
# A = (aHfs8)_1
# B = psaf_1 = s8_1
#
# B is "power_spectrum_amplitude_values" and it and its derivatives are calculated in flip_terms.py
# as it is needed by coefficients.py
# Note however that the derivatives of s8_1 in A and B are different!  A is normalized at z=0. B
# is normalized a z=z_cmb


# vv
# for a parameterization Omega_gamma: 
#      P=(a H O**g s)(a H O**g s) (P_fid/s^2_fid)

def get_partial_derivative_coefficients(
    model_type,
    parameter_values_dict,
    variant=None,
    redshift_dict=None,
):
    partial_coefficients_dict = None
    Om0 = parameter_values_dict["Om0"]
    gamma =  parameter_values_dict["gamma"]
    redshift_velocities = redshift_dict["v"]
    a = 1 / (1 + redshift_velocities)
    cosmo = FlatLambdaCDM(H0=100, Om0=Om0)
    cosmoOm = np.array(cosmo.Om(redshift_velocities))
    H = cosmo_background.H(redshift_velocities) / cosmo_background.H0

    if variant == "growth_index":


        # cosmo = FlatLambdaCDM(H0=100, Om0=parameter_values_dict["Om0"])
        # cosmoOm = np.array(cosmo.Om(redshift_velocities))
        # H = cosmo_background.H(redshift_velocities) / cosmo_background.H0

        # The Om0-gamma model f=Omega(Om0)^gamma

        f_values = f(a, Om0, gamma) #cosmoOm ** parameter_values_dict["gamma"]
        s8_values  = s8_approx(redshift_velocities, Om0, gamma)
        dfdOm0_values = dfdOm0(a, Om0, gamma)
        dfdgamma_values = dfdgamma(a, Om0, gamma)

        aHf = a * H * f_values  # aka A
        aHfs8 = aHf * s8_values


        # # now for the partials
        # dfdOm0 = (
        #     parameter_values_dict["gamma"]
        #     * f
        #     / cosmoOm
        #     * dOmdOm0(a, parameter_values_dict)
        # )
        # dfdgamma = np.log(cosmoOm) * f

        # A = aHf

        dAdOm0 = a * H * dfdOm0_values
        dAdgamma = a * H * dfdgamma_values

        Omega_m_partial_derivative_coefficients = (
            dAdOm0 * s8_values
            + aHf
            * ds8dO0_approx(
                redshift_velocities,
                Om0, gamma,
                s8_values=s8_values,
            )
        )

        gamma_partial_derivative_coefficients = (
            dAdgamma * s8_values
            + aHf
            * ds8dgamma_approx(
                redshift_velocities,
                Om0, gamma,
                s8_values=s8_values,
            )
        )

        partial_coefficients_dict = {
            "Omegam": {
                "vv": [
                    np.outer(
                        Omega_m_partial_derivative_coefficients,
                        aHfs8,
                    )
                    + np.outer(
                        aHfs8,
                        Omega_m_partial_derivative_coefficients,
                    ),
                ],
            },
            "gamma": {
                "vv": [
                    np.outer(
                        gamma_partial_derivative_coefficients,
                        aHfs8,
                    )
                    + np.outer(
                        aHfs8,
                        gamma_partial_derivative_coefficients,
                    ),
                ],
            },
        }
    elif variant == "growth_rate":
        redshift_velocities = redshift_dict["v"]
        a = 1 / (1 + redshift_velocities)
        cosmo = FlatLambdaCDM(H0=100, Om0=parameter_values_dict["Om0"])
        H = cosmo_background.H(redshift_velocities) / cosmo_background.H0

        fs8_partial_derivative_coefficients = (
            a * cosmo.H(redshift_velocities) / cosmo.H0
        )

        aHfs8 = (
            a * cosmo.H(redshift_velocities) / cosmo.H0 * parameter_values_dict["fs8"]
        )
        partial_coefficients_dict = {
            "fs8": {
                "vv": [
                    np.outer(
                        fs8_partial_derivative_coefficients,
                        aHfs8,
                    )
                    + np.outer(
                        aHfs8,
                        fs8_partial_derivative_coefficients,
                    ),
                ],
            },
        }

    return partial_coefficients_dict
