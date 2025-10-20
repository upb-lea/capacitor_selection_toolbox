"""Capacitor selection example."""

# 3rd party libraries
import numpy as np
from matplotlib import pyplot as plt

# own libraries
import cst

# capacitor requirements
capacitor_requirements = cst.SelectCapacitor(
    maximum_peak_to_peak_voltage_ripple=0.5,
    current_waveform_for_op_max_current=np.array([[0, 1.25e-6, 2.5e-6, 3.75e-6, 6e-5], [2, 1, -2, -1, 2]]),
    v_dc_for_op_max_current=700,
    current_waveform_for_op_max_voltage=np.array([[0, 1.25e-6, 2.5e-6, 3.75e-6, 6e-5], [8, 19, -8, -9, 8]]),
    v_dc_for_op_max_voltage=730,
    temperature_ambient=40,
    voltage_safety_margin_percentage=10,
    capacitor_type_list=[cst.CapacitorType.FilmCapacitor],
    maximum_number_series_capacitors=2
)

# calculate minimum required capacitance
calculated_requirements_and_values = cst.calculate_from_requirements(capacitor_requirements)
print(calculated_requirements_and_values.requirement_c_min)

# select all suitable capacitors from the database
c_db = cst.load_capacitors(capacitor_requirements.capacitor_type_list)

print(c_db.columns)


# voltage: calculate the number of needed capacitors in a series connection
c_db["in_series_needed"] = np.ceil(capacitor_requirements.v_dc_for_op_max_voltage / (c_db['V_op_125degree'] * (1 + capacitor_requirements.voltage_safety_margin_percentage / 100)))
# drop series connection capacitors more than specified
c_db = c_db.drop(c_db[c_db["in_series_needed"] > capacitor_requirements.maximum_number_series_capacitors].index)

# capacitance: calculate the number of parallel capacitors needed to meet the capacitance requirement
c_db["in_parallel_needed"] = np.ceil(calculated_requirements_and_values.requirement_c_min / (c_db["capacitance"] / c_db["in_series_needed"]))

# current: calculate the number of parallel capacitors needed to meet the current requirement
c_db["parallel_current_capacitors_needed"] = np.ceil(calculated_requirements_and_values.i_rms / c_db["i_rms_max_85degree_in_A"])
index_ripple_current = c_db["parallel_current_capacitors_needed"] > c_db["in_parallel_needed"]
c_db.loc[index_ripple_current, "in_parallel_needed"] = c_db.loc[index_ripple_current, "parallel_current_capacitors_needed"]
c_db = c_db.drop(columns=["parallel_current_capacitors_needed"])

# volume calculation
c_db["volume_total"] = c_db["in_parallel_needed"] * c_db["in_series_needed"] * c_db["volume"]

[frequency_list, current_amplitude_list, _] = cst.fft(capacitor_requirements.current_waveform_for_op_max_current, plot='no', mode='time', title='ffT input current')
c_db.loc[:, 'power_loss_per_capacitor'] = cst.power_loss_film_capacitor(c_db["ESR_85degree_in_Ohm"], frequency_list, current_amplitude_list, c_db["in_parallel_needed"])
c_db.loc[:, 'power_loss_total'] = c_db.loc[:, 'power_loss_per_capacitor'] * c_db["in_parallel_needed"] * c_db["in_series_needed"]


# plot the results
plt.scatter(c_db["volume_total"] * 1e6, c_db["power_loss_total"])
plt.xlabel("Total capacitor volume / dm³")
plt.ylabel("total capacitor loss / W")
plt.grid()
plt.show()