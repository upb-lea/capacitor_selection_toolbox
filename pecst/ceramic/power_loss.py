"""Ceramic capacitor power losses."""

# python libraries
import pathlib
import logging

# 3rd party libraries
import pandas as pd
import numpy as np

# own libraries
import pecst.constants as const

logger = logging.getLogger(__name__)

def read_ceramic_capacitor_frequency_dependent_limits(order_number: str) -> pd.DataFrame:
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
    esr_csv_filepath = pathlib.PurePath(path.parents[1], const.CERAMIC_CAPACITOR_DOWNLOAD_DIRECTORY, f"{order_number}_Imp,ESR.csv")

    df = pd.read_csv(esr_csv_filepath)

    df["esr"] = df[f"{order_number} - ESR"]
    df = df.drop(columns=["Combined - Imp", "Combined - ESR", f"{order_number} - Imp"], )

    return df


def power_loss_ceramic_capacitor(order_number: str, frequency_list: list[float], current_amplitude_list: list[float], number_parallel_capacitors: int) -> float:
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
    # read ESR file
    esr_df = read_ceramic_capacitor_frequency_dependent_limits(order_number)

    if esr_df.empty:
        logger.info(f"sort out by missing esr: {order_number}")
        esr_losses = np.nan
    else:
        esr_losses = 0.0
        for count_frequency, frequency in enumerate(frequency_list):
            # interpolate ESR at given frequency
            esr = np.interp(frequency, esr_df["Frequency (Hz)"], esr_df["esr"])

            # loss = R * I_RMS ** 2 = R * 0.5 * I_Peak ** 2 (peak due to the fft output)
            # parallel capacitors reduce the I_Peak according to the number of parallel same-value(!) capacitors
            esr_losses += esr * 0.5 * (current_amplitude_list[count_frequency] / number_parallel_capacitors) ** 2

    return esr_losses
