"""Read the capacitor database."""

# python libraries
import pathlib
import logging

# 3rd party libraries
import pandas as pd
import numpy as np

# own libraries
from pecst import constants as const
from pecst.cst_dataclasses import (CapacitanceOverFrequency, EsrOverTemperature, EsrOverFrequency, LifetimeMultiplier, RippleCurrentMultiplier,
                                   CapacitanceOverTemperature)

logger = logging.getLogger(__name__)

def get_str_value_from_str(text: str, start: str, end: str) -> str:
    """
    Get string value between start and end from a given string.

    :param text: text to find the values
    :type text: str
    :param start: string in front of the string to return
    :type start: str
    :param end: string directly after the string to return
    :type end: str
    :return: string between start and end
    :rtype: str
    """
    # Find the index of the start string
    idx1 = text.find(start)

    # Find the index of the end string, starting after the start string
    idx2 = text.find(end, idx1 + len(start))

    # Check if both delimiters are found and extract the string between them
    if idx1 != -1 and idx2 != -1:
        res = text[idx1 + len(start):idx2]
    else:
        logger.info("Delimiters not found")
    return res

def load_electrolytic_capacitors(capacitor_series_name: str) -> tuple[
    pd.DataFrame, pd.DataFrame, list[LifetimeMultiplier], list[EsrOverTemperature], list[CapacitanceOverFrequency],
        list[RippleCurrentMultiplier], list[EsrOverFrequency], list[CapacitanceOverTemperature]]:
    """
    Load electrolytic capacitors from the database.

    :param capacitor_series_name: name of the capacitor series to download
    :type capacitor_series_name: str
    :return: unified list of film capacitors
    :rtype: tuple[pandas.DataFrame, pandas.DataFrame, pandas.DataFrame]
    """
    # capacitor data
    path = pathlib.Path(__file__)

    electrolytic_capacitor_series_path = pathlib.PurePath(path.parents[1], const.ELECTROLYTIC_CAPACITOR_DATA_DIRECTORY, capacitor_series_name)
    electrolytic_capacitor_curves_path = pathlib.PurePath(path.parents[1], const.ELECTROLYTIC_CAPACITOR_DOWNLOAD_DIRECTORY, capacitor_series_name)

    database_path = pathlib.PurePath(electrolytic_capacitor_series_path, f"{capacitor_series_name}.csv")
    c_df = pd.read_csv(database_path, sep=',', decimal='.')

    # drop unused columns to reduce the data set
    c_df = c_df.drop(columns=["multiplier"])

    # transfer the datasheet given units to SI units
    c_df['area'] = (c_df["diameter_mm"].astype(float) * const.MILLI_TO_NORM / 2) ** 2 * np.pi
    c_df["diameter"] = c_df["diameter_mm"].astype(float) * const.MILLI_TO_NORM
    c_df["height"] = c_df["length_mm"].astype(float) * const.MILLI_TO_NORM
    c_df = c_df.drop(columns=["diameter_mm", "length_mm"])
    c_df['volume'] = c_df["area"].astype(float) * c_df["height"].astype(float)

    c_df['capacitance'] = c_df["C_R_100Hz_uF"].astype(float) * const.MICRO_TO_NORM
    c_df = c_df.drop(columns=["C_R_100Hz_uF"])

    c_df["i_leak_1_min_A"] = c_df["i_leak_1_min_uA"].astype(float) * const.MICRO_TO_NORM
    c_df = c_df.drop(columns=["i_leak_1_min_uA"])
    c_df["i_leak_5_min_A"] = c_df["i_leak_5_min_uA"].astype(float) * const.MICRO_TO_NORM
    c_df = c_df.drop(columns=["i_leak_5_min_uA"])

    c_df["esr_100hz_Ohm"] = c_df["esr_100hz_mOhm"].astype(float) * const.MILLI_TO_NORM
    c_df = c_df.drop(columns=["esr_100hz_mOhm"])

    # capacitance over frequency
    c_vs_f_dto_list: list[CapacitanceOverFrequency] = []
    c_vs_f_dto: CapacitanceOverFrequency
    capacitance_vs_frequency_data_files = pathlib.Path(electrolytic_capacitor_curves_path).glob(f"{capacitor_series_name}_c_vs_f_*")
    for c_vs_f_data_file in capacitance_vs_frequency_data_files:
        voltage_list = str(c_vs_f_data_file.stem).replace(f"{capacitor_series_name}_c_vs_f_", "").split("_")
        for voltage_str in voltage_list:
            c_vs_f_dto = CapacitanceOverFrequency(voltage=float(voltage_str.replace("V", "")),
                                                  capacitance_vs_frequency=pd.read_csv(
                                                      c_vs_f_data_file, decimal='.', delimiter=',', header=0, names=["frequency", "factor_capacitance"]))
            c_vs_f_dto_list.append(c_vs_f_dto)

    # capacitance over temperature
    c_vs_temperature_dto_list: list[CapacitanceOverTemperature] = []
    c_vs_temperature_dto: CapacitanceOverTemperature
    capacitance_vs_temperature_data_files = pathlib.Path(electrolytic_capacitor_curves_path).glob(f"{capacitor_series_name}_c_vs_f_*")
    for c_vs_temperature_data_file in capacitance_vs_temperature_data_files:
        voltage_list = str(c_vs_temperature_data_file.stem).replace(f"{capacitor_series_name}_c_vs_f_", "").split("_")
        for voltage_str in voltage_list:
            c_vs_temperature_dto = CapacitanceOverTemperature(voltage=float(voltage_str.replace("V", "")),
                                                              capacitance_vs_temperature=pd.read_csv(
                                                                  c_vs_temperature_data_file, decimal='.', delimiter=',', header=0,
                                                                  names=["temperature", "factor_capacitance"]))
            c_vs_temperature_dto_list.append(c_vs_temperature_dto)

    # ESR over temperature
    esr_vs_temperature_dto_list: list[EsrOverTemperature] = []
    esr_vs_temperature_dto: EsrOverTemperature
    esr_vs_temperature_data_files = pathlib.Path(electrolytic_capacitor_curves_path).glob(f"{capacitor_series_name}_factor_esr_vs_temperature_*")

    for esr_vs_temperature_data_file in esr_vs_temperature_data_files:
        voltage_list = str(esr_vs_temperature_data_file.stem).replace(f"{capacitor_series_name}_factor_esr_vs_temperature_", "").split("_")
        for voltage_str in voltage_list:
            esr_vs_temperature_dto = EsrOverTemperature(
                voltage=float(voltage_str.replace("V", "")), esr_vs_temperature=pd.read_csv(
                    esr_vs_temperature_data_file, decimal='.', delimiter=',', header=0, names=["temperature", "factor_esr"]).sort_values(by=["temperature"]))

            esr_vs_temperature_dto_list.append(esr_vs_temperature_dto)

    # ESR over frequency
    esr_vs_frequency_dto_list: list[EsrOverFrequency] = []
    esr_vs_frequency_dto: EsrOverFrequency
    esr_vs_frequency_data_files = pathlib.Path(electrolytic_capacitor_curves_path).glob(f"{capacitor_series_name}_factor_esr_vs_frequency_*")

    for esr_vs_frequency_data_file in esr_vs_frequency_data_files:
        voltage_list = str(esr_vs_frequency_data_file.stem).replace(f"{capacitor_series_name}_factor_esr_vs_frequency_", "").split("_")
        for voltage_str in voltage_list:
            esr_vs_frequency_dto = EsrOverFrequency(
                voltage=float(voltage_str.replace("V", "")), esr_vs_frequency=pd.read_csv(
                    esr_vs_frequency_data_file, decimal='.', delimiter=',', header=0, names=["frequency", "factor_esr"]).sort_values(by=["frequency"]))

            esr_vs_frequency_dto_list.append(esr_vs_frequency_dto)

    # read lifetime multipliers
    lt_multiplier_dto_list: list[LifetimeMultiplier] = []
    lt_multiplier_dto: LifetimeMultiplier
    lt_multiplier_data_files = pathlib.Path(electrolytic_capacitor_curves_path).glob(f"{capacitor_series_name}_lifetime_factor_*")
    for lt_multiplier_data_file in lt_multiplier_data_files:
        multiplier = str(lt_multiplier_data_file.stem).replace(f"{capacitor_series_name}_lifetime_factor_", "").split("_")[0]
        lt_multiplier_dto = LifetimeMultiplier(
            life_multiplier=float(multiplier), current_factor_vs_temperature=pd.read_csv(
                lt_multiplier_data_file, decimal='.', delimiter=',').sort_values(by=["temperature"]))
        lt_multiplier_dto_list.append(lt_multiplier_dto)

    # read nominal useful life
    lifetime_path = pathlib.PurePath(electrolytic_capacitor_curves_path, f"{capacitor_series_name}_lifetime.csv")
    lt_df = pd.read_csv(lifetime_path, decimal='.', delimiter=',')

    # read ripple current multipliers
    ripple_current_multiplier_dto_list: list[RippleCurrentMultiplier] = []
    ripple_current_multiplier: RippleCurrentMultiplier
    lt_multiplier_data_files = pathlib.Path(electrolytic_capacitor_curves_path).glob(f"{capacitor_series_name}_ripple_current_multiplier_*")
    for lt_multiplier_data_file in lt_multiplier_data_files:
        voltage_list = str(lt_multiplier_data_file.stem).replace(f"{capacitor_series_name}_ripple_current_multiplier_", "").split("_")
        for voltage_str in voltage_list:
            voltage = voltage_str.replace("V", "")
            ripple_current_multiplier = RippleCurrentMultiplier(
                voltage=float(voltage), current_multiplier_vs_frequency=pd.read_csv(
                    lt_multiplier_data_file, decimal='.', delimiter=',').sort_values(by=["frequency"]))
            ripple_current_multiplier_dto_list.append(ripple_current_multiplier)

    return (c_df, lt_df, lt_multiplier_dto_list, esr_vs_temperature_dto_list, c_vs_f_dto_list,
            ripple_current_multiplier_dto_list, esr_vs_frequency_dto_list, c_vs_temperature_dto_list)


if __name__ == "__main__":
    (c_df, lt_df, lt_multiplier_dto_list, esr_vs_temperature_dto_list, c_vs_f_dto_list,
        ripple_current_multiplier_dto_list, esr_vs_frequency_dto_list, c_vs_temperature_dto_list) = load_electrolytic_capacitors("058059pllsi")
    print(f"{c_df}")
