"""Detailed RMS current evaluation."""

# python libraries

# 3rd party libraries
import numpy as np

# own libraries
from pecst.power_loss import read_capacitor_frequency_dependent_limits

def current_capability_film_capacitor(order_number: str, frequency_list: list[float], current_amplitude_list: list[float], derating_factor: float) -> int:
    """
    Film capacitor power loss estimation.

    :param order_number: capacitor order number
    :type order_number: str
    :param frequency_list: frequency in Hertz in a list
    :type frequency_list: list[float]
    :param current_amplitude_list: current in ampere in a list
    :type current_amplitude_list: list[float]
    :param derating_factor: derating factor
    :type derating_factor: float
    :return: number of parallel capacitors needed due to current limit
    :rtype: int
    """
    order_number = order_number.replace("+", "K")

    # read peak current capability from file
    peak_current_capability_df = read_capacitor_frequency_dependent_limits(order_number)

    # interpolate the current capability according to the given frequencies. Note
    peak_current_capability_at_frequencies = derating_factor * np.sqrt(2) * np.interp(
        frequency_list, peak_current_capability_df["F_HZ"], peak_current_capability_df["IRMS_FINAL_AT_TOP"])

    number_parallel_capacitors_at_frequencies = np.ceil(current_amplitude_list / peak_current_capability_at_frequencies)

    number_parallel_capacitors = np.max(number_parallel_capacitors_at_frequencies)

    return int(number_parallel_capacitors)
