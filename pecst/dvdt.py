"""Maximum dv/dt calculation."""

# python libraries
import logging

# 3rd party libraries
import pandas as pd
import numpy as np

# own libraries
from pecst.cst_dataclasses import CalculatedRequirementsValues

logger = logging.getLogger(__name__)

def series_in_order_number(series_name: str, ordering_number: str) -> bool:
    """
    Check for series name in ordering number.

    :param series_name: capacitor series name
    :type series_name: str
    :param ordering_number: capacitor ordering number
    :type ordering_number: str
    :return: True if capacitor series name is in capacitor ordering number, else False
    :rtype: True
    """
    if series_name in ordering_number:
        return True
    else:
        return False

def calc_parallel_capacitors_dvdt(capacitance: float, rated_voltage: float, i_peak: float, dvdt_df: pd.DataFrame, ordering_number: str,
                                  calculated_boundaries: CalculatedRequirementsValues) -> int:
    """
    Calculate the number of parallel capacitors needed due to the maximum dv/dt requirement.

    :param capacitance: capacitance in F
    :type capacitance: float
    :param rated_voltage: capacitors rated voltage in V
    :type rated_voltage: float
    :param i_peak: peak current of the capacitor bank
    :type i_peak: float
    :param dvdt_df: dataframe with information about dv/dt limits
    :type dvdt_df: pd.DataFrame
    :param ordering_number: capacitor ordering number
    :type ordering_number: str
    :param calculated_boundaries: Calculated boundaries
    :type calculated_boundaries: CalculatedRequirementsValues
    :return: number of parallel capacitors needed due to dv/dt requirement
    :rtype: int
    """
    # get maximum allowed dv/dt per capacitor type
    dvdt_max_df = dvdt_df["dv/dt"].loc[dvdt_df.apply(
        lambda x: series_in_order_number(x["series"], ordering_number), axis=1) & (dvdt_df["rated_voltage"] == rated_voltage)]

    if len(dvdt_max_df.values) != 1:
        dvdt_max = np.nan
        logger.info("Value can not be found in the dv/dt database. Something must be wrong with the table data.\n"
                    f"{ordering_number=}, {rated_voltage=}")
    else:
        dvdt_max = float(dvdt_max_df.values[0])

    # calculate number of parallel capacitors to meet the dv/dt maximum requirement
    number_parallel_capacitors = np.ceil(i_peak / dvdt_max / capacitance)

    return int(number_parallel_capacitors)
