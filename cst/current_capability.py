"""Detailed RMS current evaluation."""

# python libraries

# 3rd party libraries
import numpy as np

# own libraries
from cst.power_loss import read_capacitor_frequency_dependent_limits

def current_capability_film_capacitor(order_number: str, frequency_list: list[float], current_amplitude_list: list[float], number_parallel_capacitors: int) \
        -> float:
    """
    Film capacitor power loss estimation.

    :param order_number: capacitor order number
    :type order_number: str
    :param frequency_list: frequency in Hertz in a list
    :type frequency_list: list[float]
    :param current_amplitude_list: current in ampere in a list
    :type current_amplitude_list: list[float]
    :param number_parallel_capacitors: number of parallel capacitors to estimate the current per capacitor
    :type number_parallel_capacitors: int
    :return: loss of a single capacitor in Watt
    :rtype: float
    """
    order_number = order_number.replace("+", "K")

    # read peak current capability from file
    peak_current_capability_df = read_capacitor_frequency_dependent_limits(order_number)

    capacitor_suitable: bool = False

    # interpolate the current capability according to the given frequencies. Note
    peak_current_capability_at_frequencies = np.sqrt(2) * np.interp(
        frequency_list, peak_current_capability_df["F_HZ"], peak_current_capability_df["IRMS_FINAL_AT_TOP"])

    if (peak_current_capability_at_frequencies / number_parallel_capacitors > current_amplitude_list).all():
        capacitor_suitable = True
    else:
        capacitor_suitable = False

    return capacitor_suitable
