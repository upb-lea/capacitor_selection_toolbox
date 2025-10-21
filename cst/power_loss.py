"""Capacitor power loss calculation."""

# def read_leakage_current(operating_voltage: float, temperature_ambient: float) -> float:
#     leakage_current = 1
#     return leakage_current
#
# def read_equal_series_resistance(temperature_ambient: float, frequency) -> float:
#     equal_series_resistance = 1
#     return equal_series_resistance

def power_loss_film_capacitor(esr: float, frequency_list: list[float], current_amplitude_list: list[float], number_parallel_capacitors: int) -> float:
    """
    Film capacitor power loss estimation.

    :param esr: capacitor equivalent series resistance (ESR) in ohm
    :type esr: float
    :param frequency_list: frequency in Hertz in a list
    :type frequency_list: list[float]
    :param current_amplitude_list: current in ampere in a list
    :type current_amplitude_list: list[float]
    :param number_parallel_capacitors: number of parallel capacitors to estimate the current per capacitor
    :type number_parallel_capacitors: int
    :return: loss of a single capacitor in Watt
    :rtype: float
    """
    esr_losses = 0.0
    for count_frequency, _ in enumerate(frequency_list):
        # loss = R * I_RMS ** 2 = R * 0.5 * I_Peak ** 2 (peak due to the fft output)
        # parallel capacitors reduce the I_Peak according to the number of parallel same-value(!) capacitors
        esr_losses += esr * 0.5 * (current_amplitude_list[count_frequency] / number_parallel_capacitors) ** 2

    return esr_losses
