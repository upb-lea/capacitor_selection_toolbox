"""Capacitor power loss calculation."""

# python libraries
import pathlib

# 3rd party libraries
import pandas as pd
import numpy as np

# own libraries
import pecst.constants as const

# def read_leakage_current(operating_voltage: float, temperature_ambient: float) -> float:
#     leakage_current = 1
#     return leakage_current

def read_capacitor_frequency_dependent_limits(order_number: str) -> pd.DataFrame:
    """
    Read the frequency-dependent limits from csv file to a pandas data frame.

    This contains:
     * frequency-dependent equivalent series resistance (ESR)
     * frequency-dependent current capability
     * frequency-dependent AC RMS voltage

    :param order_number: order number
    :type order_number: str
    :return: frequency-dependent ESR, current capability and AC RMS voltage in a pandas data frame
    :rtype: pandas.DataFrame
    """
    path = pathlib.Path(__file__)

    # path to esr file
    esr_csv_filepath = pathlib.PurePath(path.parents[0], "esr_downloads", f"{order_number}.csv")

    df = pd.read_csv(esr_csv_filepath)

    df["esr"] = df["ESR_FINAL"] * const.MILLI_TO_NORM
    df = df.drop(columns=["ESR_FINAL", "EDITION_DATE"])

    return df

def power_loss_film_capacitor(order_number: str, frequency_list: list[float], current_amplitude_list: list[float], number_parallel_capacitors: int) -> float:
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
    order_number = order_number.replace("*", "")

    # read ESR file
    esr_df = read_capacitor_frequency_dependent_limits(order_number)

    esr_losses = 0.0
    for count_frequency, frequency in enumerate(frequency_list):
        # interpolate ESR at given frequency
        esr = np.interp(frequency, esr_df["F_HZ"], esr_df["esr"])

        # loss = R * I_RMS ** 2 = R * 0.5 * I_Peak ** 2 (peak due to the fft output)
        # parallel capacitors reduce the I_Peak according to the number of parallel same-value(!) capacitors
        esr_losses += esr * 0.5 * (current_amplitude_list[count_frequency] / number_parallel_capacitors) ** 2

    return esr_losses
