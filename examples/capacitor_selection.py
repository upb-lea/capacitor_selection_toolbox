"""Capacitor selection example."""

# 3rd party libraries
import numpy as np
import pandas as pd
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
c_db, sh_db, c_derating = cst.load_capacitors(capacitor_requirements.capacitor_type_list)

def look_for_derating_factor(ambient_temperature: float, df_derating: pd.DataFrame) -> float:
    """
    Read the capacitors temperature derating factor from a look-up table.

    :param ambient_temperature: ambient temperature in degree Celsius
    :param df_derating: dataframe with temperature derating information
    :return: derating factor
    """
    derating_factor: float
    if ambient_temperature < df_derating["temperature"][0]:
        derating_factor = df_derating["derating_factor"][0]
    elif ambient_temperature > df_derating["temperature"][-1]:
        derating_factor = df_derating["derating_factor"][-1]
    else:
        derating_factor = np.interp(ambient_temperature, df_derating["temperature"], df_derating["derating_factor"])
    return derating_factor


derating_factor = look_for_derating_factor(ambient_temperature=capacitor_requirements.temperature_ambient, df_derating=c_derating)

# voltage: calculate the number of needed capacitors in a series connection
c_db["in_series_needed"] = np.ceil(capacitor_requirements.v_dc_for_op_max_voltage / (c_db['V_op_125degree'] * \
                                                                                     (1 + capacitor_requirements.voltage_safety_margin_percentage / 100)))
# drop series connection capacitors more than specified
c_db = c_db.drop(c_db[c_db["in_series_needed"] > capacitor_requirements.maximum_number_series_capacitors].index)

# capacitance: calculate the number of parallel capacitors needed to meet the capacitance requirement
c_db["in_parallel_needed"] = np.ceil(calculated_requirements_and_values.requirement_c_min / (c_db["capacitance"] / c_db["in_series_needed"]))

# current: calculate the number of parallel capacitors needed to meet the current requirement
c_db["parallel_current_capacitors_needed"] = np.ceil(calculated_requirements_and_values.i_rms / c_db["i_rms_max_85degree_in_A"] / derating_factor)
index_ripple_current = c_db["parallel_current_capacitors_needed"] > c_db["in_parallel_needed"]
c_db.loc[index_ripple_current, "in_parallel_needed"] = c_db.loc[index_ripple_current, "parallel_current_capacitors_needed"]
c_db = c_db.drop(columns=["parallel_current_capacitors_needed"])

# volume calculation
c_db["volume_total"] = c_db["in_parallel_needed"] * c_db["in_series_needed"] * c_db["volume"]

# loss calculation
[frequency_list, current_amplitude_list, _] = cst.fft(capacitor_requirements.current_waveform_for_op_max_current, plot='no',
                                                      mode='time', title='ffT input current')
c_db.loc[:, 'power_loss_per_capacitor'] = (
    cst.power_loss_film_capacitor(c_db["ESR_85degree_in_Ohm"], frequency_list, current_amplitude_list, c_db["in_parallel_needed"]))
c_db.loc[:, 'power_loss_total'] = c_db.loc[:, 'power_loss_per_capacitor'] * c_db["in_parallel_needed"] * c_db["in_series_needed"]

def look_for_thermal_coefficient(df: pd.DataFrame, width: float, length: float, height: float) -> float:
    """
    Read the thermal equivalent self-heating coefficient.

    :param df: dataframe with equivalent self-heating coefficient based on the capacitor housing dimensions.
    :param width: capacitor width in meter
    :param length: capacitor length in meter
    :param height: capacitor height in meter
    :return: thermal equivalent coefficient
    """
    thermal_coefficient = df["g_in_W_degreeCelsius"].loc[(df["width_in_m"] == width) & (df["length_in_m"] == length) & (df["height_in_m"] == height)]

    print(thermal_coefficient.values[0])

    if len(thermal_coefficient.values) != 1:
        raise ValueError("Value can not be found in the thermal coefficient database. Something must be wrong with the table data.")

    return float(thermal_coefficient.values[0])


look_for_thermal_coefficient(sh_db, 22e-3, 31.5e-3, 36.5e-3)

# self heating calculation
c_db['g_in_W_degreeCelsius'] = c_db.apply(lambda x: look_for_thermal_coefficient(sh_db, x["width_in_m"], x["length_in_m"], x["height_in_m"]), axis=1)
c_db["delta_temperature"] = c_db['power_loss_total'] / c_db['g_in_W_degreeCelsius']

# check for temperature derating

c_db["delta_temperature_max"] = derating_factor ** 2 * 15

# drop too high self-heated capacitors
c_db = c_db.drop(c_db[c_db["delta_temperature"] > c_db["delta_temperature_max"]].index)


# plot the results
plt.scatter(c_db["volume_total"] * 1e6, c_db["power_loss_total"])
plt.xlabel("Total capacitor volume / dm³")
plt.ylabel("total capacitor loss / W")
plt.grid()
plt.show()
