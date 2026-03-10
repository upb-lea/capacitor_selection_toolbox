"""Calculations for the balancing resistors."""

# 3rd party libraries
import numpy as np

# own libraries

def generate_resistor_list(e_series_basic_list, potency_list):
    """
    Generate a e-series of resistor-values over some decades.

    :param e_series_basic_list: e-series-basic list [1.....9.9]
    :type e_series_basic_list: list
    :param potency_list: list of potency to generate result-list
    :type potency_list: list
    :return: full e-series list of resistors
    :rtype: list
    """
    e_series_resistor_list = []
    for potency in potency_list:
        for resistor_basic_value in e_series_basic_list:
            e_series_resistor_list.append(resistor_basic_value * 10 ** potency)
    return e_series_resistor_list

def calculate_r_parallel_max(leakage_current_per_capacitor: float, parallel_capacitors: int, series_capacitors: int, dc_link_voltage: float) -> float:
    """
    Calculate the maximum parallel resistance allowed to make sure that the resistor current is 10 times higher than the total leakage current.

    :param leakage_current_per_capacitor: leakage current per resistor in A
    :type leakage_current_per_capacitor: float
    :param parallel_capacitors: Number of parallel capacitors
    :type parallel_capacitors: int
    :param series_capacitors: Number of capacitors in series
    :type series_capacitors: int
    :param dc_link_voltage: DC link operating voltage
    :type dc_link_voltage: float
    :return: maximum value of parallel resistance
    """
    if series_capacitors == 1:
        return np.nan
    else:
        resistor_current = 10 * leakage_current_per_capacitor * parallel_capacitors
        resistor_voltage = dc_link_voltage / series_capacitors
        return resistor_voltage / resistor_current

def look_for_closest_smaller_resistance(r_max: float, resistor_list: list) -> float:
    """
    Look for the closest smaller resistance in resistor_list than the given one r_max.

    :param r_max: maximum resistance in Ohm
    :type r_max: float
    :param resistor_list: list of resistors
    :type resistor_list: list
    :return: closest and smaller resistor in the list
    """
    if np.isnan(r_max):
        return np.nan
    else:
        index_r_closest = np.searchsorted(resistor_list, [r_max, ], side='right')[0] - 1
        r_closest = resistor_list[index_r_closest]
        return float(r_closest)

def loss_per_resistor(voltage_per_capacitor: float, resistance: float) -> float:
    """
    Calculate the power loss per resistor.

    Return 0 W in case of no resistance (np.nan) given.
    :param voltage_per_capacitor: voltage per capacitor in V
    :type voltage_per_capacitor: float
    :param resistance: Resistance in Ohm
    :type resistance: float
    :return: loss per capacitor in W
    """
    if np.isnan(resistance):
        return 0
    else:
        return voltage_per_capacitor ** 2 / resistance


if __name__ == "__main__":
    r_closest = look_for_closest_smaller_resistance(r_max=105, resistor_list=[80, 90, 100, 110, 120])
    print(f"{r_closest=}")
