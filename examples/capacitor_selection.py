"""Capacitor selection example."""

# 3rd party libraries
import numpy as np
from matplotlib import pyplot as plt

# own libraries
import cst

# capacitor requirements
capacitor_requirements = cst.SelectCapacitor(
    maximum_peak_to_peak_voltage_ripple=0.5,
    current_waveform_for_op_max_current=np.array([[0, 1.25e-6, 2.5e-6, 3.75e-6, 6e-5], [10, 20, -10, -20, 10]]),
    v_dc_for_op_max_current=700,
    current_waveform_for_op_max_voltage=np.array([[0, 1.25e-6, 2.5e-6, 3.75e-6, 6e-5], [8, 18, -8, -18, 8]]),
    v_dc_for_op_max_voltage=730,
    temperature_ambient=40,
    voltage_safety_margin_percentage=10,
    capacitor_type_list=[cst.CapacitorType.FilmCapacitor],
    maximum_number_series_capacitors=2
)

# calculate minimum required capacitance
calculated_requirements_and_values = cst.calculate_from_requirements(capacitor_requirements)

# select all suitable capacitors from the database
c_db = cst.load_capacitors(capacitor_requirements.capacitor_type_list)

print(c_db.columns)


# voltage: calculate the number of needed capacitors in a series connection
c_db["in_series_needed"] = np.ceil(capacitor_requirements.v_dc_for_op_max_voltage / (c_db['V_op_125degree'] * (1 + capacitor_requirements.voltage_safety_margin_percentage / 100)))
# drop series connection capacitors more than specified
c_db = c_db.drop(c_db[c_db["in_series_needed"] > capacitor_requirements.maximum_number_series_capacitors].index)

# capacitance: calculate the number of parallel capacitors needed to meet the capacitance requirement
#c_db["in_parallel_needed"] = np.ceil()


# current: calculate the

c_db_filtered = c_db.loc[c_db['V_op_125degree'] > capacitor_requirements.v_dc_for_op_max_current]
c_db_filtered = c_db_filtered.loc[c_db_filtered['i_rms_max_85degree_in_A'] > calculated_requirements_and_values.i_rms]






# [frequency_list, current_amplitude_list, _] = cst.fft(example_waveform, plot='no', mode='time', title='ffT input current')
# c_db_filtered.loc[:, 'power_loss'] = cst.power_loss_film_capacitor(c_db_filtered["ESR_85degree_in_Ohm"], frequency_list, current_amplitude_list)