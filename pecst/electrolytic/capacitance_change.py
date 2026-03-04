"""Capacitance change due to temperature and frequency."""

# 3rd party libraries
import numpy as np

# own libraries
from pecst.cst_dataclasses import CapacitanceOverFrequency, CapacitanceOverTemperature

def calc_capacitance_factor_frequency(c_vs_f_dto_list: list[CapacitanceOverFrequency], rated_voltage: float,
                                      base_frequency: float) -> float:
    """
    Get the factor of capacitance loss due to the frequency.

    :param c_vs_f_dto_list: List of capacitance vs. frequency DTOs
    :type c_vs_f_dto_list: list[CapacitanceOverFrequency]
    :param rated_voltage: Rated voltage in V
    :type rated_voltage: float
    :param base_frequency: Base frequency of the current ripple in Hz
    :type base_frequency: float
    :return: factor of capacitance loss
    """
    for c_vs_f_dto_sweep in c_vs_f_dto_list:
        if c_vs_f_dto_sweep.voltage == rated_voltage:
            c_vs_f_dto = c_vs_f_dto_sweep

    capacitance_factor = np.interp(base_frequency, c_vs_f_dto.capacitance_vs_frequency["frequency"], c_vs_f_dto.capacitance_vs_frequency["factor_capacitance"])
    return float(capacitance_factor)

def calc_capacitance_factor_temperature(c_vs_t_dto_list: list[CapacitanceOverTemperature], rated_voltage: float,
                                        temperature: float) -> float:
    """
    Get the factor of capacitance loss due to the temperature.

    :param c_vs_t_dto_list: List of capacitance vs. temperature DTOs
    :type c_vs_t_dto_list: list[CapacitanceOverTemperature]
    :param rated_voltage: Rated voltage in V
    :type rated_voltage: float
    :param temperature: Ambient temperature in °C
    :type temperature: float
    :return: factor of capacitance loss
    """
    c_vs_t_dto = None
    for c_vs_t_dto_sweep in c_vs_t_dto_list:
        if c_vs_t_dto_sweep.voltage == rated_voltage:
            c_vs_t_dto = c_vs_t_dto_sweep
    if c_vs_t_dto is None:
        # the 40V and 50V capacitor is not defined in the 056057psmsi datasheet. Use 1.0 as a factor and assume no capacitance change.
        return 1.0

    capacitance_factor = np.interp(temperature, c_vs_t_dto.capacitance_vs_temperature["temperature"],
                                   c_vs_t_dto.capacitance_vs_temperature["factor_capacitance"])
    return float(capacitance_factor)
