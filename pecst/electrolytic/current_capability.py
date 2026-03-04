"""Calculate the electrolytic capacitor current capability."""

# 3rd party libraries
import numpy as np

# own libraries
from pecst.cst_dataclasses import RippleCurrentMultiplier

def _geometric_current_sum(rms_current_list):
    sum_rms_currents = 0.0
    for rms_current in rms_current_list:
        sum_rms_currents += rms_current ** 2
    return np.sqrt(sum_rms_currents)


def parallel_electrolytic_capacitors_lifetime_current_capability(voltage: float, frequency_list: list[float], current_amplitude_list: list[float],
                                                                 ripple_current_multiplier_dto_list: list[RippleCurrentMultiplier], i_rated: float,
                                                                 factor_i_actual_i_rated: float) -> float:
    """
    Estimate the number of parallel electrolytic capacitors necessary.

    Example how to use the 'frequency conversion table': https://www.vishay.com/docs/28356/alucapsintrobcc.pdf

    :param voltage: capacitor rated voltage in V
    :type voltage: float
    :param frequency_list: frequency in Hertz in a list
    :type frequency_list: list[float]
    :param current_amplitude_list: current in ampere in a list
    :type current_amplitude_list: list[float]
    :param ripple_current_multiplier_dto_list: List of RippleCurrentMultiplier DTOs
    :type ripple_current_multiplier_dto_list: RippleCurrentMultiplier
    :param i_rated: capacitor rated RMS current in A
    :type i_rated: float
    :param factor_i_actual_i_rated: Factor i_actual_rms/i_rated_rms from the Nomogram
    :type factor_i_actual_i_rated: float
    :return: number of parallel capacitors needed due to current limit
    :rtype: int
    """
    # read peak current capability from file
    for ripple_current_multiplier_dto in ripple_current_multiplier_dto_list:
        if ripple_current_multiplier_dto.voltage == voltage:
            break

    # interpolate current multipliers
    multiplier_list = np.interp(frequency_list, ripple_current_multiplier_dto.current_multiplier_vs_frequency["frequency"],
                                ripple_current_multiplier_dto.current_multiplier_vs_frequency["current_multiplier"])
    # fix current multipliers when exceed the maximum given frequency
    max_frequency = ripple_current_multiplier_dto.current_multiplier_vs_frequency["frequency"].values[-1]
    current_multiplier_at_max_frequency = ripple_current_multiplier_dto.current_multiplier_vs_frequency["current_multiplier"].values[-1]
    multiplier_list[frequency_list > max_frequency] = current_multiplier_at_max_frequency

    # estimate the number of parallel capacitors necessary
    number_parallel_capacitors: int = 1
    while True:
        weighted_current_rms_list_per_capacitor = np.array(current_amplitude_list) / np.sqrt(2) / number_parallel_capacitors / multiplier_list
        weighted_rms_current_per_capacitor = _geometric_current_sum(weighted_current_rms_list_per_capacitor)

        if weighted_rms_current_per_capacitor <= i_rated * factor_i_actual_i_rated:
            break
        else:
            number_parallel_capacitors += 1

    return number_parallel_capacitors
