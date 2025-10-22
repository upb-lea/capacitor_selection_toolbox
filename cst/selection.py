"""Misc calculations."""

# 3rd party libraries
import numpy as np
import pandas as pd

# own libraries
from cst.cst_dataclasses import CapacitorRequirements, CalculatedRequirementsValues
from cst.functions import fft
from cst.read_capacitor_database import load_capacitors
from cst.power_loss import power_loss_film_capacitor

def calculate_from_requirements(capacitor_requirements: CapacitorRequirements) -> CalculatedRequirementsValues:
    """
    Values and requirements for further calculations needed from the input values.

    :param capacitor_requirements: capacitor requirements and input values in a DTO
    :type capacitor_requirements: CapacitorRequirements
    :return: calculated requirements and values (from input parameters)
    :rtype: CalculatedRequirementsValues
    """
    new_time_sample_rate = np.linspace(capacitor_requirements.current_waveform_for_op_max_current[0][0],
                                       capacitor_requirements.current_waveform_for_op_max_current[0][-1], 5000)
    new_current_sample_rate = np.interp(new_time_sample_rate, capacitor_requirements.current_waveform_for_op_max_current[0],
                                        capacitor_requirements.current_waveform_for_op_max_current[1])
    time_step = new_time_sample_rate[1] - new_time_sample_rate[0]
    positive_capacitor_charge = np.sum(new_current_sample_rate[new_current_sample_rate > 0] * time_step)
    c_min = positive_capacitor_charge / capacitor_requirements.maximum_peak_to_peak_voltage_ripple

    i_rms = np.sqrt(np.mean(capacitor_requirements.current_waveform_for_op_max_current[1] ** 2))

    return CalculatedRequirementsValues(
        requirement_c_min=c_min,
        i_rms=i_rms
    )

def get_temperature_current_derating_factor(ambient_temperature: float, df_derating: pd.DataFrame) -> float:
    """
    Read the capacitors temperature derating factor from a look-up table (from data sheet).

    :param ambient_temperature: ambient temperature in degree Celsius
    :type ambient_temperature: float
    :param df_derating: dataframe with temperature derating information
    :type df_derating: pd.DataFrame
    :return: derating factor
    :rtype: float
    """
    derating_factor: float
    if ambient_temperature < df_derating["temperature"][0]:
        derating_factor = df_derating["derating_factor"][0]
    elif ambient_temperature > df_derating["temperature"][-1]:
        derating_factor = df_derating["derating_factor"][-1]
    else:
        derating_factor = np.interp(ambient_temperature, df_derating["temperature"], df_derating["derating_factor"])
    return derating_factor

def get_equivalent_heat_coefficient(df: pd.DataFrame, width: float, length: float, height: float) -> float:
    """
    Read the thermal equivalent heat coefficient (from data sheet).

    :param df: dataframe with equivalent self-heating coefficient based on the capacitor housing dimensions.
    :type df: pandas.DataFrame
    :param width: capacitor width in meter
    :type width: float
    :param length: capacitor length in meter
    :type length: float
    :param height: capacitor height in meter
    :type height: float
    :return: thermal equivalent coefficient
    :rtype: float
    """
    thermal_coefficient = df["g_in_W_degreeCelsius"].loc[(df["width_in_m"] == width) & (df["length_in_m"] == length) & (df["height_in_m"] == height)]

    if len(thermal_coefficient.values) != 1:
        raise ValueError("Value can not be found in the thermal coefficient database. Something must be wrong with the table data.")

    return float(thermal_coefficient.values[0])

def select_capacitors(c_requirements: CapacitorRequirements) -> pd.DataFrame:
    """
    Select suitable capacitors for the given application.

    Function works as a "big filter":
     - reads in all available capacitor data depending on the given capacitor type
     - use series connection up to a maximum given number of capacitors to reach the operating voltage
     - adds parallel capacitors to reach the minimum required capacitance value
     - adds parallel capacitors to not raise the current limit per capacitor
     - considers current derating according to the ambient temperature
     - considers self-heating derating according to the ambient temperature
     - sort out non-working designs/construction (raising voltage limits, raising temperature limits)

    The resulting pandas data frame contains the whole Pareto plane with all technically possible capacitor designs.
    Filtering e.g. for the Pareto front must be done in a separate step by the user.

    :param c_requirements: capacitor requirements
    :type c_requirements: CapacitorRequirements
    :return: pandas data frame with all possible capacitors.
    :rtype: pandas.DataFrame
    """
    # calculate minimum required capacitance and RMS current
    calculated_boundaries = calculate_from_requirements(c_requirements)

    # select all suitable capacitors including derating and thermal information from the database
    c_db, c_thermal, c_derating = load_capacitors(c_requirements.capacitor_type_list)

    derating_factor = get_temperature_current_derating_factor(ambient_temperature=c_requirements.temperature_ambient, df_derating=c_derating)

    # check for temperature derating
    delta_temperature_max = derating_factor ** 2 * 15

    virtual_inner_max_temperature = c_requirements.temperature_ambient + delta_temperature_max
    c_db['V_op_max_virt'] = c_db.apply(lambda x: np.interp(virtual_inner_max_temperature, [85, 105, 125],
                                                           [x["V_R_85degree"], x["V_op_105degree"], x["V_op_125degree"]]), axis=1)

    # voltage: calculate the number of needed capacitors in a series connection
    c_db["in_series_needed"] = np.ceil(c_requirements.v_dc_for_op_max_voltage / (c_db['V_op_max_virt'] * \
                                                                                 (1 + c_requirements.voltage_safety_margin_percentage / 100)))
    # drop series connection capacitors more than specified
    c_db = c_db.drop(c_db[c_db["in_series_needed"] > c_requirements.maximum_number_series_capacitors].index)

    # capacitance: calculate the number of parallel capacitors needed to meet the capacitance requirement
    c_db["in_parallel_needed"] = np.ceil(
        calculated_boundaries.requirement_c_min / (c_db["capacitance"] * (1 - c_requirements.capacitor_tolerance / 100) / c_db["in_series_needed"]))

    # current: calculate the number of parallel capacitors needed to meet the current requirement
    c_db["parallel_current_capacitors_needed"] = np.ceil(calculated_boundaries.i_rms / c_db["i_rms_max_85degree_in_A"] / derating_factor)
    index_ripple_current = c_db["parallel_current_capacitors_needed"] > c_db["in_parallel_needed"]
    c_db.loc[index_ripple_current, "in_parallel_needed"] = c_db.loc[index_ripple_current, "parallel_current_capacitors_needed"]
    c_db = c_db.drop(columns=["parallel_current_capacitors_needed"])

    # volume calculation
    c_db["volume_total"] = c_db["in_parallel_needed"] * c_db["in_series_needed"] * c_db["volume"]

    # loss calculation
    [frequency_list, current_amplitude_list, _] = fft(c_requirements.current_waveform_for_op_max_current, plot='no',
                                                      mode='time', title='ffT input current')

    c_db["power_loss_per_capacitor"] = c_db.apply(lambda x: power_loss_film_capacitor(x["ordering code"], frequency_list, current_amplitude_list,
                                                                                      x["in_parallel_needed"]), axis=1)

    c_db.loc[:, 'power_loss_total'] = c_db.loc[:, 'power_loss_per_capacitor'] * c_db["in_parallel_needed"] * c_db["in_series_needed"]

    # self heating calculation
    # g_in_W_degreeCelsius is the equivalent heat coefficient according to the data sheet
    c_db['g_in_W_degreeCelsius'] = c_db.apply(lambda x: get_equivalent_heat_coefficient(c_thermal, x["width_in_m"], x["length_in_m"], x["height_in_m"]), axis=1)
    c_db["delta_temperature"] = c_db['power_loss_total'] / c_db['g_in_W_degreeCelsius']

    # drop too high self-heated capacitors
    c_db = c_db.drop(c_db[c_db["delta_temperature"] > delta_temperature_max].index)

    return c_db
