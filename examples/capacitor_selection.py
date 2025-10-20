

# 3rd party libraries
import numpy as np
from matplotlib import pyplot as plt

# own libraries
import cst

# capacitor requirements
capacitor_requirements = cst.SelectCapacitor(
    maximum_peak_to_peak_voltage_ripple=0.5,
    current_waveform_operation_point_1=np.array([[0, 1.25e-6, 2.5e-6, 3.75e-6, 6e-5],[10, 20, -10, -20, 10]]),
    v_dc_operating_point_1=700,
    current_waveform_operation_point_2=np.array([[0, 1.25e-6, 2.5e-6, 3.75e-6, 6e-5],[8, 18, -8, -18, 8]]),
    v_dc_operating_point_2=730,
    temperature_ambient=40,
)


# calculate minimum required capacitance
new_time_sample_rate = np.linspace(capacitor_requirements.current_waveform_operation_point_1[0][0], capacitor_requirements.current_waveform_operation_point_1[0][-1], 5000)
new_current_sample_rate = np.interp(new_time_sample_rate, capacitor_requirements.current_waveform_operation_point_1[0], capacitor_requirements.current_waveform_operation_point_1[1])
time_step = new_time_sample_rate[1] - new_time_sample_rate[0]
print(f"{time_step=}")
positive_capacitor_charge = np.sum(new_current_sample_rate[new_current_sample_rate > 0] * time_step)
print(f"{positive_capacitor_charge=}")
c_min = positive_capacitor_charge / capacitor_requirements.maximum_peak_to_peak_voltage_ripple

i_rms = np.sqrt(np.mean(capacitor_requirements.current_waveform_operation_point_1[1] ** 2))
print(f"{i_rms=}")


# select all suitable capacitors from the database
c_db = cst.load_dc_film_capacitors()
c_db_filtered = c_db.loc[c_db['V_op_125degree'] > capacitor_requirements.v_dc_operating_point_1]
c_db_filtered = c_db_filtered.loc[c_db_filtered['i_rms_max_85degree_in_A'] > i_rms]



# [frequency_list, current_amplitude_list, _] = cst.fft(example_waveform, plot='no', mode='time', title='ffT input current')
# c_db_filtered.loc[:, 'power_loss'] = cst.power_loss_film_capacitor(c_db_filtered["ESR_85degree_in_Ohm"], frequency_list, current_amplitude_list)