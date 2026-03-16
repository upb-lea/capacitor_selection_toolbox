"""Read the resistor database."""

# python libraries
import pathlib
import logging

# 3rd party libraries
import pandas as pd
import numpy as np

# own libraries
from pecst import constants as const

logger = logging.getLogger(__name__)

def load_resistors(resistor_series_name: str) -> pd.DataFrame:
    """
    Load resistors from the database.

    :param resistor_series_name: name of the resistor series to download
    :type resistor_series_name: str
    :return: unified list of resistors
    :rtype: tuple[pandas.DataFrame]
    """
    # resistor data
    path = pathlib.Path(__file__)

    resistor_series_path = pathlib.PurePath(path.parents[1], const.RESISTORS_DATA_DIRECTORY, resistor_series_name)

    database_path = pathlib.PurePath(resistor_series_path, f"{resistor_series_name}.csv")
    r_df = pd.read_csv(database_path, sep=',', decimal='.')

    # transfer the datasheet given units to SI units
    r_df['area'] = r_df["diameter"].astype(float) * r_df["length"].astype(float)
    r_df['volume'] = (r_df["diameter"].astype(float) / 2) ** 2 * np.pi * r_df["length"].astype(float)

    return r_df


if __name__ == "__main__":
    resistor_df = load_resistors("ac")
    print(f"{resistor_df}")
