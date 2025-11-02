"""Capacitor lifetime_h consideration."""

# 3rd party libraries
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from matplotlib import pyplot as plt

# own libraries
from cst.cst_dataclasses import LifetimeDerating

class FatigueCurve:
    """
    Base class for a fatigue curve.

    source:
    https://www.robsiegwart.com/interpolating-logarithmic-plots-for-fatigue-analysis.html

    points : list
            A list containing (lifetime_h,voltage) data point pairs (2+)
    """

    def __init__(self, points):
        self.N, self.S = list(zip(*points, strict=True))
        self.N = np.asarray(self.N)
        self.S = np.asarray(self.S)
        self.logN = np.log10(self.N)
        self.logS = np.log10(self.S)

class SemiLogCurve(FatigueCurve):
    """Class for logarithmic interpolation."""

    def __init__(self, points):
        super().__init__(points)
        self.getS_f = interp1d(self.logN, self.S)
        self.getN_f = interp1d(self.S, self.logN)

    def get_voltage(self, lifetime: float) -> np.ndarray:
        """
        Interpolate stress from cycles.

        :param lifetime: capacitor lifetime_h
        :type lifetime: float
        """
        try:
            S = self.getS_f(np.log10(lifetime))
        except:
            S = np.nan
        return np.array([S])

    __call__ = get_voltage

def voltage_rating_due_to_lifetime(target_lifetime: float, operating_temperature: float, voltage_rating: float,
                                   lt_dto_list: list[LifetimeDerating], is_plot: bool = False) -> float:
    """
    Voltage dearting due to capacitor lifetime_h.

    :param target_lifetime: capacitor target lifetime_h in hours
    :type target_lifetime: float
    :param operating_temperature: operating temperature in degree Celsius
    :type operating_temperature: float
    :param voltage_rating: capacitor operating voltage in V
    :type voltage_rating: float
    :param lt_dto_list: lifetime_h DTO list
    :type lt_dto_list: list[LifetimeDerating]
    :param is_plot: True to show interpolation plot
    :type is_plot: bool
    :return: voltage
    :rtype: float
    """
    temperature_lower: float = 0
    temperature_higher: float = 500
    for lt_dto in lt_dto_list:
        # find temperature below and temperature above the operating temperature
        if lt_dto.voltage == voltage_rating:
            if operating_temperature <= lt_dto.temperature < temperature_higher:
                temperature_higher = lt_dto.temperature
            if operating_temperature >= lt_dto.temperature > temperature_lower:
                temperature_lower = lt_dto.temperature
    if temperature_higher == 500:
        temperature_higher = temperature_lower
    if temperature_lower == 0:
        temperature_lower = temperature_higher

    # interpolate between both temperatures
    for lt_dto in lt_dto_list:
        if lt_dto.voltage == voltage_rating and lt_dto.temperature == temperature_lower:
            df_lower = lt_dto.lifetime
        if lt_dto.voltage == voltage_rating and lt_dto.temperature == temperature_higher:
            df_higher = lt_dto.lifetime

    # geometric interpolation for the new lifetime_h curve for the new temperature
    df_mid = pd.DataFrame()
    df_mid["lifetime"] = np.sqrt(df_lower["lifetime"] * df_higher["lifetime"])
    df_mid["voltage"] = np.sqrt(df_lower["voltage"] * df_higher["voltage"])

    # logarithmic voltage interpolation for the voltage
    zip_curve = zip(df_mid["lifetime"], df_mid["voltage"], strict=True)
    curve = SemiLogCurve(list(zip_curve))
    voltage = curve.get_voltage(target_lifetime)

    if is_plot:
        plt.semilogx(df_lower["lifetime_h"], df_lower["voltage"], label="lower")
        plt.semilogx(df_higher["lifetime_h"], df_higher["voltage"], label="higher")
        plt.semilogx(df_mid["lifetime_h"], df_mid["voltage"], label="df_mid")
        plt.plot(target_lifetime, voltage, 'ro')
        plt.grid()
        plt.show()

    return float(voltage)


if __name__ == '__main__':
    import cst
    c_df, sh_df, c_derating, dvdt_df, l_dto_list = cst.load_dc_film_capacitors("B3271*P")
    voltage = voltage_rating_due_to_lifetime(target_lifetime=300_000, operating_temperature=86,
                                             lt_dto_list=l_dto_list, voltage_rating=825)
    print(f"{voltage=}")
