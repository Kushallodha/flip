import os
import numpy as np
import pandas as pd
from flip import fitter, plot_utils, utils
from flip.covariance import covariance, contraction
from pkg_resources import resource_filename

from flip.covariance.rcrk24.flip_terms import *

def main():
    flip_base = resource_filename("flip", ".")
    data_path = os.path.join(flip_base, "data")

    ### Load data
    sn_data = pd.read_parquet(os.path.join(data_path, "velocity_data.parquet"))

    sn_data = sn_data[np.array(sn_data["status"]) != False]
    sn_data = sn_data[np.array(sn_data["status"]) != None]

# coordinates_velocity = np.array([sn_data["ra"], sn_data["dec"], sn_data["rcom_zobs"]])
    coordinates_velocity = np.array([sn_data["ra"], sn_data["dec"], sn_data["rcom_zobs"], sn_data["zobs"]])
    data_velocity = sn_data.to_dict("list")
    for key in data_velocity.keys():
        data_velocity[key] = np.array(data_velocity[key])
    data_velocity["velocity"] = data_velocity.pop("vpec")
    data_velocity["velocity_error"] = np.zeros_like(data_velocity["velocity"])


    ktt, ptt = np.loadtxt(os.path.join(data_path, "power_spectrum_tt.txt"))
    kmt, pmt = np.loadtxt(os.path.join(data_path, "power_spectrum_mt.txt"))
    kmm, pmm = np.loadtxt(os.path.join(data_path, "power_spectrum_mm.txt"))

    sigmau_fiducial = 15

    power_spectrum_dict = {"vv": [[ktt, ptt * utils.Du(ktt, sigmau_fiducial) ** 2]]}

    ### Compute covariance
    size_batch = 10_000
    number_worker = 16

    variant = "growth_rate"  # can be replaced by growth_index
    covariance_fit = covariance.CovMatrix.init_from_flip(
        "rcrk24",
        # "carreres23",
        "velocity",
        power_spectrum_dict,
        coordinates_velocity=coordinates_velocity,
        size_batch=size_batch,
        number_worker=number_worker,
        power_spectrum_amplitude_function=power_spectrum_amplitude_function_growth_rate,
        variant=variant,
    )


    ### Load fitter
    likelihood_type = "multivariate_gaussian"
    likelihood_properties = {
        "inversion_method": "cholesky",
        "velocity_type": "saltfit",
        "velocity_estimator": "full",
    }


    parameter_dict = {
        "fs8": {
            "value": 0.4,
            "limit_low": 0.0,
            "limit_up": 1.0,
            "fixed": False,
        },
        "sigv": {
            "value": 200,
            "limit_low": 0.0,
            "limit_up": 300,
            "fixed": False,
        },
        "alpha": {
            "value": 0.1,
            "limit_low": 0.05,
            "limit_up": 0.15,
            "fixed": False,
        },
        "beta": {
            "value": 3.0,
            "limit_low": 1.5,
            "limit_up": 4.5,
            "fixed": False,
        },
        "M_0": {
            "value": -19,
            "limit_low": -21,
            "limit_up": -18,
            "fixed": False,
        },
        "sigma_M": {
            "value": 0.1,
            "limit_low": 0.0,
            "limit_up": 1.0,
            "fixed": False,
        },
    }

    parameter_dict = {
        "f": {
            "value": 0.45570516784429815/0.832,
            "limit_low": 0.0,
            "limit_up": 1.0/0.832,
            "fixed": True,
        },
        "Om0": {
            "value": 0.3,
            "limit_low": 0.0,
            "limit_up": 1.0,
            "fixed": False,
        },
        "gamma": {
            "value": 0.55,
            "limit_low": 0.0,
            "limit_up": 1.0,
            "fixed": False,
        },
        "sigv": {
            "value": 200,
            "limit_low": 0.0,
            "limit_up": 300,
            "fixed": False,
        },
        "alpha": {
            "value": 0.,
            "limit_low": 0.05,
            "limit_up": 0.15,
            "fixed": False,
        },
        "beta": {
            "value": .0,
            "limit_low": 1.5,
            "limit_up": 4.5,
            "fixed": False,
        },
        "M_0": {
            "value": -19,
            "limit_low": -21,
            "limit_up": -18,
            "fixed": False,
        },
        "sigma_M": {
            "value": 0.1,
            "limit_low": 0.0,
            "limit_up": 1.0,
            "fixed": False,
        },
    }

    minuit_fitter = fitter.FitMinuit.init_from_covariance(
        covariance_fit,
        data_velocity,
        parameter_dict,
        likelihood_type=likelihood_type,
        likelihood_properties=likelihood_properties,
    )
    minuit_fitter.run()
    return

if __name__ == '__main__':
    main()
    # minuit_fitter.run()
