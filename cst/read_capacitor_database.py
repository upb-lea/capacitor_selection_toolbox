"""Read the capacitor database."""

# python libraries
import pathlib
import logging

# 3rd party libraries
import pandas as pd
import numpy as np

# own libraries
from cst import constants as const
from cst.cst_dataclasses import LifetimeDerating

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

def load_dc_film_capacitors(capacitor_series_name: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[LifetimeDerating]]:
    """
    Load dc film capacitors from the database.

    :param capacitor_series_name: name of the capacitor series to download
    :type capacitor_series_name: str
    :return: unified list of film capacitors
    :rtype: tuple[pandas.DataFrame, pandas.DataFrame, pandas.DataFrame]
    """
    # capacitor data
    path = pathlib.Path(__file__)

    database_path = pathlib.PurePath(path.parents[0], f"{capacitor_series_name}.csv")
    c_df = pd.read_csv(database_path, sep=';', decimal='.')

    # drop unused columns to reduce the data set
    c_df = c_df.drop(columns=["multiplier_1", "multiplier_2", "MOQ", "p1_in_mm"])

    # transfer the datasheet given units to SI units
    c_df['area'] = c_df["width_in_mm"].astype(float) * const.MILLI_TO_NORM * c_df["length_in_mm"].astype(float) * const.MILLI_TO_NORM
    c_df["width_in_m"] = c_df["width_in_mm"].astype(float) * const.MILLI_TO_NORM
    c_df["height_in_m"] = c_df["height_in_mm"].astype(float) * const.MILLI_TO_NORM
    c_df["length_in_m"] = c_df["length_in_mm"].astype(float) * const.MILLI_TO_NORM
    c_df = c_df.drop(columns=["width_in_mm", "height_in_mm", "length_in_mm"])
    c_df['volume'] = c_df["width_in_m"].astype(float) * c_df["height_in_m"].astype(float) * c_df["length_in_m"].astype(float)

    c_df['capacitance'] = c_df["capacitance_in_uf"].astype(float) * const.MICRO_TO_NORM
    c_df = c_df.drop(columns=["capacitance_in_uf"])

    c_df["ESR_85degree_in_Ohm"] = c_df["ESR_85degree_in_mOhm"].astype(float) * const.MILLI_TO_NORM
    c_df = c_df.drop(columns=["ESR_85degree_in_mOhm"])

    c_df["ESL_in_H"] = c_df["ESL_in_nH"].astype(float) * const.NANO_TO_NORM
    c_df = c_df.drop(columns=["ESL_in_nH"])

    c_df["i_rms_max_85degree_in_A"] = c_df["i_rms_max_85degree_in_A"].astype(float)

    c_df["ordering code"] = c_df["ordering code"].apply(lambda x: x.replace("*", ""))

    # self heating data
    self_heating_path = pathlib.PurePath(path.parents[0], f"{capacitor_series_name}_self_heating.csv")
    sh_df = pd.read_csv(self_heating_path, sep=';', decimal=',')

    sh_df["width_in_m"] = sh_df["width_in_mm"].astype(float) * const.MILLI_TO_NORM
    sh_df["height_in_m"] = sh_df["height_in_mm"].astype(float) * const.MILLI_TO_NORM
    sh_df["length_in_m"] = sh_df["length_in_mm"].astype(float) * const.MILLI_TO_NORM
    sh_df["g_in_W_degreeCelsius"] = sh_df["g_in_mW_degreeCelsius"].astype(float) * const.MILLI_TO_NORM
    sh_df = sh_df.drop(columns=["width_in_mm", "height_in_mm", "length_in_mm", "g_in_mW_degreeCelsius"])

    # derating data
    database_path = pathlib.PurePath(path.parents[0], f"{capacitor_series_name}_derating.csv")
    c_derating = pd.read_csv(database_path, sep=';', decimal=',')

    # lifetime_h data
    lt_dto_list: list[LifetimeDerating] = []
    lt_dto: LifetimeDerating
    lifetime_data_files = pathlib.Path(pathlib.PurePath(path.parents[0])).glob(f"{capacitor_series_name}_lifetime*")
    for lifetime_data_file in lifetime_data_files:
        voltage_str = get_str_value_from_str(lifetime_data_file.stem, start="lifetime_", end="V_")
        temperature = float(get_str_value_from_str(lifetime_data_file.stem, start="V_", end="degree"))

        if voltage_str == "x":
            # get all different rated temperatures
            unique_voltage_values = c_df["V_R_85degree"].unique()
            for unique_voltage_value in unique_voltage_values:
                lifetime_df = pd.read_csv(lifetime_data_file, decimal=',', delimiter=';')
                # derating factor is maximum 1. May greater due to digitizing error from datasheet. Clip value to 1.
                lifetime_df["voltage"] = np.clip(lifetime_df["voltage"], a_min=0, a_max=1)

                # modify lifetime_h df, as there is a factor and no absolute voltage level given
                lifetime_df["voltage"] = unique_voltage_value * lifetime_df["voltage"]
                lt_dto = LifetimeDerating(temperature=temperature, voltage=unique_voltage_value,
                                          lifetime=lifetime_df)
                lt_dto_list.append(lt_dto)
        else:
            lt_dto = LifetimeDerating(temperature=temperature, voltage=float(voltage_str),
                                      lifetime=pd.read_csv(lifetime_data_file, decimal=',', delimiter=';'))
            lt_dto_list.append(lt_dto)

    return c_df, sh_df, c_derating, lt_dto_list


if __name__ == "__main__":
    # c_df, sh_df, c_derating, l_dto_list = load_dc_film_capacitors("B3272*AGT")
    c_df, sh_df, c_derating, l_dto_list = load_dc_film_capacitors("B3277*P")

    print(f"{len(l_dto_list)=}")
