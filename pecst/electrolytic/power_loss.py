"""Electrolytic capacitor power loss calculation."""

# python libraries

# 3rd party libraries
import numpy as np
import pandas as pd

# own libraries
from pecst.cst_dataclasses import EsrOverTemperature, EsrOverFrequency

def calc_leakage_currents(rated_capacitance: float, rated_voltage: float) -> pd.Series[float]:
    """
    Get the 5 minutes leakage current and the permanent leakage current depending on the capacitance and on the rated voltage.

    :param rated_capacitance: rated capacitance in F
    :type rated_capacitance: float
    :param rated_voltage: rated voltage in V
    :type rated_voltage: float
    :return: leakage current for 5 minutes and permanent value
    """
    # 5 minutes value
    i_leak_5_min = 0.002 * rated_capacitance * rated_voltage + 4e-6
    # the permanent leakage current is about 20% of the 5-minutes leakage current: https://www.vishay.com/docs/28356/alucapsintrobcc.pdf
    i_leak_permanent = 0.2 * i_leak_5_min
    return pd.Series([i_leak_5_min, i_leak_permanent])

def power_loss_per_electrolytic_capacitor(esr_nominal: float, capacitor_rated_voltage: float, ambient_temperature: float, frequency_list: list[float],
                                          current_amplitude_list: list[float], number_parallel_capacitors: int,
                                          esr_vs_frequency_dto_list: list[EsrOverFrequency], esr_vs_temperature_dto_list: list[EsrOverTemperature],
                                          capacitor_nominal_capacitance: float, operating_voltage_per_capacitor: float) -> float:
    """
    Film capacitor power loss estimation.

    :param esr_nominal: nominal equivalent series resistance in ohm
    :type esr_nominal: float
    :param capacitor_rated_voltage: rated voltage of a single capacitor in V
    :type capacitor_rated_voltage: float
    :param ambient_temperature: ambient temperature in degree celcius
    :type ambient_temperature: float
    :param frequency_list: frequency in Hertz in a list
    :type frequency_list: list[float]
    :param current_amplitude_list: current in ampere in a list
    :type current_amplitude_list: list[float]
    :param number_parallel_capacitors: number of parallel capacitors to estimate the current per capacitor
    :type number_parallel_capacitors: int
    :param esr_vs_frequency_dto_list: ESR(frequency) in a DTO list
    :type esr_vs_frequency_dto_list: list[EsrOverFrequeny]
    :param esr_vs_temperature_dto_list: ESR(temperature) in a DTO list
    :type esr_vs_temperature_dto_list: list[EsrOverTemperature]
    :param capacitor_nominal_capacitance: nominal capacitance in F
    :type capacitor_nominal_capacitance: float
    :param operating_voltage_per_capacitor: operating voltage in V
    :type operating_voltage_per_capacitor: float
    :return: loss of a single capacitor in Watt
    :rtype: float
    """
    # read ESR file
    for esr_vs_frequency_data_object in esr_vs_frequency_dto_list:
        if esr_vs_frequency_data_object.voltage == capacitor_rated_voltage:
            esr_vs_frequency_dto = esr_vs_frequency_data_object

    for esr_vs_temperature_data_object in esr_vs_temperature_dto_list:
        if esr_vs_temperature_data_object.voltage == capacitor_rated_voltage:
            esr_vs_temperature_dto = esr_vs_temperature_data_object

    temperature_factor = np.interp(
        ambient_temperature, esr_vs_temperature_dto.esr_vs_temperature["temperature"], esr_vs_temperature_dto.esr_vs_temperature["factor_esr"])

    # losses by current ripple per frequency
    esr_losses = 0.0
    for count_frequency, frequency in enumerate(frequency_list):
        # interpolate ESR at given frequency
        frequency_factor = np.interp(frequency, esr_vs_frequency_dto.esr_vs_frequency["frequency"], esr_vs_frequency_dto.esr_vs_frequency["factor_esr"])
        esr = esr_nominal * frequency_factor * temperature_factor

        # loss = R * I_RMS ** 2 = R * 0.5 * I_Peak ** 2 (peak due to the fft output)
        # parallel capacitors reduce the I_Peak according to the number of parallel same-value(!) capacitors
        esr_losses += esr * 0.5 * (current_amplitude_list[count_frequency] / number_parallel_capacitors) ** 2

    # losses by leakage current
    _, permanent_leakage_current = calc_leakage_currents(rated_capacitance=capacitor_nominal_capacitance, rated_voltage=capacitor_rated_voltage)
    leakage_losses = permanent_leakage_current * operating_voltage_per_capacitor

    return esr_losses + leakage_losses


if __name__ == "__main__":
    _, permanent_leakage_current = calc_leakage_currents(rated_capacitance=470e-6, rated_voltage=400)
    leakage_loss = permanent_leakage_current * 380
    print(f"{permanent_leakage_current=}")
    print(f"{leakage_loss=}")
