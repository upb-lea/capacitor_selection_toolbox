"""Capacitor lifetime_h consideration."""

# python libraries
import logging

# 3rd party libraries
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from matplotlib import pyplot as plt

# own libraries
from pecst.cst_dataclasses import LifetimeDerating

logger = logging.getLogger(__name__)

def get_voltage_from_semilogx_lifetime(lifetime: float, lifetime_vec: pd.Series, voltage_vec: pd.Series) -> np.ndarray:
    """
    Semilogarithmic interpolation from voltage over lifetime curve to get the maximum allowed voltage (to reach the lifetime).

    close to:
    https://www.robsiegwart.com/interpolating-logarithmic-plots-for-fatigue-analysis.html
    :param lifetime: lifetime in hours
    :type lifetime: float
    :param lifetime_vec: vector lifetime
    :type lifetime_vec: pd.Series
    :param voltage_vec: vector voltage
    :type voltage_vec: pd.Series
    :return:
    """
    log_lifetime_vec = np.log10(lifetime_vec)
    try:
        f = interp1d(log_lifetime_vec, voltage_vec)
        voltage = f(np.log10(lifetime))
    except:
        voltage = np.nan
    return np.array(voltage)

def voltage_rating_due_to_lifetime(target_lifetime: float, operating_temperature: float, voltage_rating: float,
                                   lt_dto_list: list[LifetimeDerating], is_debug: bool = False) -> float:
    """
    Voltage derating due to capacitor lifetime_h.

    :param target_lifetime: capacitor target lifetime_h in hours
    :type target_lifetime: float
    :param operating_temperature: operating temperature in degree Celsius
    :type operating_temperature: float
    :param voltage_rating: capacitor operating voltage in V
    :type voltage_rating: float
    :param lt_dto_list: List of lifetime_h DTOs (lifetime curve depending on voltage and temperature)
    :type lt_dto_list: list[LifetimeDerating]
    :param is_debug: True to show interpolation plot
    :type is_debug: bool
    :return: voltage
    :rtype: float
    """
    temperature_lower: float = 0
    temperature_higher: float = 500
    for lt_dto in lt_dto_list:
        # find temperature below and temperature above the operating temperature
        if lt_dto.voltage == voltage_rating:
            logger.debug(f"Lifetime DTO {lt_dto.voltage} V.")
            if operating_temperature <= lt_dto.temperature < temperature_higher:
                temperature_higher = lt_dto.temperature
            if operating_temperature >= lt_dto.temperature > temperature_lower:
                temperature_lower = lt_dto.temperature
    if temperature_higher == 500:
        temperature_higher = temperature_lower
    if temperature_lower == 0:
        temperature_lower = temperature_higher
    logger.debug(f"{temperature_lower=} °C, {temperature_higher=} °C.")

    # get the dataframes of lower and higher temperatures (closest to the operating point)
    for lt_dto in lt_dto_list:
        if lt_dto.voltage == voltage_rating and lt_dto.temperature == temperature_lower:
            df_lower = lt_dto.lifetime
        if lt_dto.voltage == voltage_rating and lt_dto.temperature == temperature_higher:
            df_higher = lt_dto.lifetime

    # interpolate between both temperatures multiple times using bisection
    # experimentally figure out c_min
    temperature_start = temperature_lower
    temperature_stop = temperature_higher
    higher_df = df_higher.copy()
    lower_df = df_lower.copy()
    delta_temperature = 100
    # temperature error should be less than 1 degree Celsius
    while delta_temperature > 1:
        # interpolated temperature
        temperature_mid = (temperature_start + temperature_stop) / 2

        # geometric interpolation for the new lifetime_h curve for the new temperature
        df_mid = pd.DataFrame()
        df_mid["lifetime"] = np.sqrt(lower_df["lifetime"] * higher_df["lifetime"])
        df_mid["voltage"] = np.sqrt(lower_df["voltage"] * higher_df["voltage"])

        # bisection new start conditions
        if operating_temperature > temperature_mid:
            temperature_start = temperature_mid
            lower_df["lifetime"] = df_mid["lifetime"]
            lower_df["voltage"] = df_mid["voltage"]
        elif operating_temperature == temperature_mid:
            break
        else:
            temperature_stop = temperature_mid
            higher_df["lifetime"] = df_mid["lifetime"]
            higher_df["voltage"] = df_mid["voltage"]

        # calculate temperature error
        delta_temperature = np.abs(operating_temperature - temperature_mid)

    # logarithmic voltage interpolation for the voltage
    voltage = get_voltage_from_semilogx_lifetime(target_lifetime, df_mid["lifetime"], df_mid["voltage"])

    if is_debug:
        plt.semilogx(df_lower["lifetime"], df_lower["voltage"], label=f"{temperature_lower} °C")
        plt.semilogx(df_higher["lifetime"], df_higher["voltage"], label=f"{temperature_higher} °C")
        plt.semilogx(df_mid["lifetime"], df_mid["voltage"], label=f"{temperature_mid} °C")
        plt.title(f"Operating temperature = {operating_temperature} °C")
        plt.plot(target_lifetime, voltage, 'ro', label="voltage at target lifetime")
        plt.legend()
        plt.grid()
        plt.show()

    logger.debug(f"{voltage=}")

    return voltage.astype(float)


if __name__ == '__main__':
    import pecst

    logger = logging.getLogger(__name__)
    hdlr = logging.StreamHandler()
    fhdlr = logging.FileHandler("myapp.log")
    logger.addHandler(hdlr)
    logger.addHandler(fhdlr)
    logger.setLevel(logging.DEBUG)

    c_df, sh_df, c_derating, dvdt_df, l_dto_list = pecst.load_dc_film_capacitors("B3271*P")
    voltage = voltage_rating_due_to_lifetime(target_lifetime=300_000, operating_temperature=86,
                                             lt_dto_list=l_dto_list, voltage_rating=825, is_debug=True)
    print(f"{voltage=}")
