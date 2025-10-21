"""Read the capacitor database."""

# python libraries
import pathlib

# 3rd party libraries
import pandas as pd

# own libraries
from cst.cst_dataclasses import CapacitorType
from cst import constants as const


def load_capacitors(capacitor_type_list: list[CapacitorType]) -> pd.DataFrame:
    """
    Load the capacitors from the given types, e.g. film capacitors, electrolytic capacitors, ...

    Returns all loaded capacitor classes in a single list.

    :param capacitor_type_list: list of capacitor types to load
    :type capacitor_type_list: list[CapacitorType]
    :return: pandas data frame with all loaded capacitors
    :rtype: pandas.DataFrame
    """
    for capacitor_type in capacitor_type_list:
        if capacitor_type == CapacitorType.FilmCapacitor:
            c_df = load_dc_film_capacitors()
        elif capacitor_type == CapacitorType.ElectrolyticCapacitor:
            raise NotImplementedError

    return c_df

def load_dc_film_capacitors() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load dc film capacitors from the database.

    :return: unified list of film capacitors
    :rtype: tuple[pandas.DataFrame, pandas.DataFrame, pandas.DataFrame]
    """
    path = pathlib.Path(__file__)
    database_path = pathlib.PurePath(path.parents[0], "B3271*P.csv")

    c_df = pd.read_csv(database_path, sep=';', decimal='.')

    # drop unused columns to reduce the data set
    c_df = c_df.drop(columns=["multiplier_1", "multiplier_2", "MOQ", "p1_in_mm"])

    # transfer the datasheet given units to SI units
    c_df['volume'] = c_df["width_in_mm"].astype(float) * c_df["height_in_mm"].astype(float) * c_df["length_in_mm"].astype(float) * \
        const.QUBIC_MILLI_METER_TO_QUBIC_METER
    c_df['area'] = c_df["width_in_mm"].astype(float) * const.MILLI_TO_NORM * c_df["length_in_mm"].astype(float) * const.MILLI_TO_NORM
    c_df["width_in_m"] = c_df["width_in_mm"].astype(float) * const.MILLI_TO_NORM
    c_df["height_in_m"] = c_df["height_in_mm"].astype(float) * const.MILLI_TO_NORM
    c_df["length_in_m"] = c_df["length_in_mm"].astype(float) * const.MILLI_TO_NORM
    c_df = c_df.drop(columns=["width_in_mm", "height_in_mm", "length_in_mm"])

    c_df['capacitance'] = c_df["capacitance_in_uf"].astype(float) * const.MICRO_TO_NORM
    c_df = c_df.drop(columns=["capacitance_in_uf"])

    c_df["ESR_85degree_in_Ohm"] = c_df["ESR_85degree_in_mOhm"].astype(float) * const.MILLI_TO_NORM
    c_df = c_df.drop(columns=["ESR_85degree_in_mOhm"])

    c_df["ESL_in_H"] = c_df["ESL_in_nH"].astype(float) * const.NANO_TO_NORM
    c_df = c_df.drop(columns=["ESL_in_nH"])

    c_df["i_rms_max_85degree_in_A"] = c_df["i_rms_max_85degree_in_A"].astype(float)

    self_heating_path = pathlib.PurePath(path.parents[0], "B3271*P_self_heating.csv")
    sh_df = pd.read_csv(self_heating_path, sep=';', decimal=',')

    sh_df["width_in_m"] = sh_df["width_in_mm"].astype(float) * const.MILLI_TO_NORM
    sh_df["height_in_m"] = sh_df["height_in_mm"].astype(float) * const.MILLI_TO_NORM
    sh_df["length_in_m"] = sh_df["length_in_mm"].astype(float) * const.MILLI_TO_NORM
    sh_df["g_in_W_degreeCelsius"] = sh_df["g_in_mW_degreeCelsius"].astype(float) * const.MILLI_TO_NORM
    sh_df = sh_df.drop(columns=["width_in_mm", "height_in_mm", "length_in_mm", "g_in_mW_degreeCelsius"])

    database_path = pathlib.PurePath(path.parents[0], "B3271*P_derating.csv")
    c_derating = pd.read_csv(database_path, sep=';', decimal=',')

    return c_df, sh_df, c_derating


if __name__ == "__main__":
    load_dc_film_capacitors()
