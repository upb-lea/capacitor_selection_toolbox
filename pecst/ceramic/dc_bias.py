"""Consider the dc bias of ceramic capacitors."""

# python libraries
import pathlib

# 3rd party libraries
import pandas as pd
import numpy as np

# own libraries
import pecst.constants as const

def read_ceramic_capacitor_dc_bias(order_number: str) -> pd.DataFrame:
    """
    Read the voltage-dependent capacitance change from csv file to a pandas data frame.

    :param order_number: order number
    :type order_number: str
    :return: voltage-dependent capacitance change in percent in a pandas data frame
    :rtype: pandas.DataFrame
    """
    path = pathlib.Path(__file__)

    # path to esr file
    dc_bias_csv_filepath = pathlib.PurePath(path.parents[1], const.CERAMIC_CAPACITOR_DOWNLOAD_DIRECTORY, f"{order_number}_Vbias.csv")

    df = pd.read_csv(dc_bias_csv_filepath)

    df["change_percent"] = df[f"{order_number} - Change %"]
    # Note: This is a bug in the kemet ksim tool. The csv voltage is wrongly stored as frequency. But it is voltage (the values makes sense).
    # So it is changed to voltage here.
    df["voltage"] = df["Frequency (Hz)"]
    df = df.drop(columns=["Frequency (Hz)",f"{order_number} - Change %"])

    return df

def dc_bias_series_parallel_connection(order_number: str, capacitance: float, dc_link_voltage: float, number_min_capacitors_in_series: int,
                                       number_max_capacitors_in_series: int, target_capacitance: float) -> pd.Series:
    """
    Estimate the minimum number of needed capacitors (series/parallel connection) considering the dc bias.

    :param order_number: ordering number
    :return: in_series_needed, in_parallel_needed
    """
    # read ESR file
    dc_bias_df = read_ceramic_capacitor_dc_bias(order_number)

    # test series capacitor connections from 1 to 'number_max_capacitors_in_series' capacitors
    series_connection = np.arange(number_min_capacitors_in_series, number_max_capacitors_in_series + 1)

    best_combination_in_series_needed: int = 1000
    best_combination_in_parallel_needed: int = 1000

    for number_series_capacitors in series_connection:
        # calculate the capacitance at the voltage (DC-bias)
        dc_voltage_per_capacitor = dc_link_voltage / number_series_capacitors
        capacitance_change_percent_at_voltage = np.interp(dc_voltage_per_capacitor, dc_bias_df["voltage"], dc_bias_df["change_percent"])
        capacitance_at_voltage = capacitance * (1 - capacitance_change_percent_at_voltage / 100)

        in_parallel_needed = np.ceil(target_capacitance * number_series_capacitors / capacitance_at_voltage)

        number_capacitors = number_series_capacitors * in_parallel_needed

        # figure out the combination where a minimum number of capacitors are needed
        if number_capacitors < (best_combination_in_series_needed * best_combination_in_parallel_needed):
            best_combination_in_series_needed = number_series_capacitors
            best_combination_in_parallel_needed = in_parallel_needed

    return pd.Series([best_combination_in_series_needed, best_combination_in_parallel_needed])
