"""Electrolytic capacitor power loss calculation."""

# python libraries

# 3rd party libraries
import numpy as np

# own libraries
from pecst.cst_dataclasses import EsrOverTemperature, EsrOverFrequency

def power_loss_electrolytic_capacitor(esr_nominal: float, capacitor_nominal_voltage: float, ambient_temperature: float, frequency_list: list[float],
                                      current_amplitude_list: list[float], number_parallel_capacitors: int,
                                      esr_vs_frequency_dto_list: list[EsrOverFrequency], esr_vs_temperature_dto_list: list[EsrOverTemperature]) -> float:
    """
    Film capacitor power loss estimation.

    :param esr_nominal: nominal equivalent series resistance in ohm
    :type esr_nominal: float
    :param capacitor_nominal_voltage: nominal voltage of a single capacitor in V
    :type capacitor_nominal_voltage: float
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
    :return: loss of a single capacitor in Watt
    :rtype: float
    """
    # read ESR file
    for esr_vs_frequency_data_object in esr_vs_frequency_dto_list:
        if esr_vs_frequency_data_object.voltage == capacitor_nominal_voltage:
            esr_vs_frequency_dto = esr_vs_frequency_data_object

    for esr_vs_temperature_data_object in esr_vs_temperature_dto_list:
        if esr_vs_temperature_data_object.voltage == capacitor_nominal_voltage:
            esr_vs_temperature_dto = esr_vs_temperature_data_object

    temperature_factor = np.interp(
        ambient_temperature, esr_vs_temperature_dto.esr_vs_temperature["temperature"], esr_vs_temperature_dto.esr_vs_temperature["factor_esr"])

    esr_losses = 0.0
    for count_frequency, frequency in enumerate(frequency_list):
        # interpolate ESR at given frequency
        frequency_factor = np.interp(frequency, esr_vs_frequency_dto.esr_vs_frequency["frequency"], esr_vs_frequency_dto.esr_vs_frequency["factor_esr"])
        esr = esr_nominal * frequency_factor * temperature_factor

        # loss = R * I_RMS ** 2 = R * 0.5 * I_Peak ** 2 (peak due to the fft output)
        # parallel capacitors reduce the I_Peak according to the number of parallel same-value(!) capacitors
        esr_losses += esr * 0.5 * (current_amplitude_list[count_frequency] / number_parallel_capacitors) ** 2

    return esr_losses
