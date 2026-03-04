"""Capacitance change due to temperature and frequency."""

# 3rd party libraries
import numpy as np

# own libraries
from pecst.cst_dataclasses import CapacitanceOverFrequency

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
