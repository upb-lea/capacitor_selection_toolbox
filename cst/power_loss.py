"""Capacitor power loss calculation."""

from cst.functions import fft

def read_leakage_current(operating_voltage: float, temperature_ambient: float) -> float:
    leakage_current = 1
    return leakage_current

def read_equal_series_resistance(temperature_ambient: float, frequency) -> float:
    equal_series_resistance = 1
    return equal_series_resistance

def power_loss_electrolyte_capacitor(current_waveform_time_amplitude_list: list, temperature_ambient: float, operating_voltage):

    leakage_losses = read_leakage_current(temperature_ambient=temperature_ambient, operating_voltage=operating_voltage)

    [frequency_list, current_amplitude_list, _] = fft(current_waveform_time_amplitude_list, plot='no', mode='time', title='ffT input current')

    esr_losses = 0
    for count_frequency, frequency in enumerate(frequency_list):
        esr_at_frequency = read_equal_series_resistance(temperature_ambient=temperature_ambient, frequency=frequency)
        esr_losses += esr_at_frequency * 0.5 * current_amplitude_list[count_frequency] ** 2

    return leakage_losses + esr_losses

def power_loss_film_capacitor(esr: float, frequency_list, current_amplitude_list, number_parallel_capacitors: int):
    esr_losses = 0
    for count_frequency, frequency in enumerate(frequency_list):
        esr_losses += esr * 0.5 * (current_amplitude_list[count_frequency] / number_parallel_capacitors) ** 2

    return esr_losses






