"""Calculations for the balancing resistors."""

# 3rd party libraries
import numpy as np
import pandas as pd

# own libraries
from pecst.resistor.read_resistor_database import load_resistors

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

def calculate_r_parallel_max(leakage_current_per_capacitor_5min: float, parallel_capacitors: int, series_capacitors: int,
                             dc_link_voltage: float, rated_voltage: float) -> float:
    """
    Calculate the maximum parallel resistance allowed to make sure that the resistor current is 10 times higher than the total leakage current.

    :param leakage_current_per_capacitor_5min: leakage current per capacitor after 5 minutes in A
    :type leakage_current_per_capacitor_5min: float
    :param parallel_capacitors: Number of parallel capacitors
    :type parallel_capacitors: int
    :param series_capacitors: Number of capacitors in series
    :type series_capacitors: int
    :param rated_voltage: rated capacitor voltage in V
    :type rated_voltage: float
    :param dc_link_voltage: DC link operating voltage
    :type dc_link_voltage: float
    :return: maximum value of parallel resistance
    """
    if series_capacitors == 1:
        return np.nan
    else:
        resistance = (series_capacitors * rated_voltage - dc_link_voltage) / (leakage_current_per_capacitor_5min * parallel_capacitors)
        return resistance


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


def look_for_closest_higher_power(power: float, power_list: list) -> float:
    """
    Look for the closest higher power in power_list than the given power.

    :param power: power in W
    :type power: float
    :param power_list: list of power
    :type power_list: list
    :return: closest and higher power in the list
    """
    if np.isnan(power):
        return np.nan
    else:
        index_r_closest = np.searchsorted(power_list, [power, ], side='right')[0]
        p_closest = power_list[index_r_closest]
        return float(p_closest)

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

def select_resistor_area_volume(power_loss: float, ambient_temperature: float,
                                r_df: pd.DataFrame) -> pd.Series[float]:
    """
    Select the resistor area and volume for a given resistor power dissipation.

    :param power_loss: resistor power loss in W
    :type power_loss: float
    :param ambient_temperature: ambient temperature in °C
    :type ambient_temperature: float
    :param r_df: resistor database
    :type r_df: pd.Dataframe
    :return: area, volume
    """
    if power_loss == 0:
        area = 0.0
        volume = 0.0
    else:
        # interpolate power due to ambient temperature
        r_df["power_rating_at_ambient_temperature"] = r_df.apply(lambda x: np.interp(
            ambient_temperature, [-40, 40, 70], [x["power_40_degree"], x["power_40_degree"], x["power_70_degree"]]), axis=1)

        # look for the closest higher temperature
        higher_rated_power = look_for_closest_higher_power(power_loss, r_df["power_rating_at_ambient_temperature"].to_list())

        # select resistor area and volume
        area = r_df.loc[r_df["power_rating_at_ambient_temperature"] == higher_rated_power]["area"].values[0]
        volume = r_df.loc[r_df["power_rating_at_ambient_temperature"] == higher_rated_power]["volume"].values[0]
    return pd.Series([area, volume])

def calculate_r_max_discharge(v_dc: float, n_parallel: int, n_series: int, c: float) -> float:
    """
    Discharge the DC link within 3 minutes below 50 volts. Calculate the maximum allowed resistance.

    :param v_dc: DC link voltage in V
    :type v_dc: float
    :param n_parallel: number of parallel capacitors
    :type n_parallel: int
    :param n_series: number of series capacitors
    :type n_series: int
    :param c: capacitor capacitance in F
    :type c: float
    :return:
    """
    # constants
    t_discharge = 180
    v_safety = 50

    v_start = v_dc / n_series
    v_end = v_safety / n_series
    r_parallel: float = -t_discharge / (n_parallel * c * np.log(v_end / v_start))

    return r_parallel


if __name__ == "__main__":
    r_closest = look_for_closest_smaller_resistance(r_max=105, resistor_list=[80, 90, 100, 110, 120])
    print(f"{r_closest=}")
    resistor_df = load_resistors("ac")
    [area, volume] = select_resistor_area_volume(2.5, 70, resistor_df)
    print(f"{area=}")
    print(f"{volume=}")
