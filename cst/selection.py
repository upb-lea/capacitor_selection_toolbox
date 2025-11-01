"""Misc calculations."""
# python libraries
import logging
import pathlib

# 3rd party libraries
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

# own libraries
from cst.cst_dataclasses import CapacitorRequirements, CalculatedRequirementsValues
from cst.functions import fft
from cst.read_capacitor_database import load_dc_film_capacitors
from cst.power_loss import power_loss_film_capacitor
import cst.constants as const
import cst.cost_models as cost
from cst.current_capability import current_capability_film_capacitor

logger = logging.getLogger(__name__)


def integrate(time: np.ndarray, data: np.ndarray) -> np.ndarray:
    """
    Integrate a given time series.

    :param time: list of time
    :type time: np.ndarray
    :param data: list of data
    :type data: np.ndarray
    """
    time_step = time[1] - time[0]
    integrated_data = np.array([])
    for count, _ in enumerate(time):
        if count == 0:
            # set first energy value to zero
            integrated_data = np.append(integrated_data, 0)
        else:
            # using euler method
            integrated_time_step = (np.nan_to_num(data[count]) + np.nan_to_num(data[count - 1])) / 2 * time_step
            integrated_data = np.append(integrated_data, integrated_data[-1] + integrated_time_step)

    return integrated_data

def calculate_from_requirements(capacitor_requirements: CapacitorRequirements, debug: bool = False) -> CalculatedRequirementsValues:
    """
    Values and requirements for further calculations needed from the input values.

    :param capacitor_requirements: capacitor requirements and input values in a DTO
    :type capacitor_requirements: CapacitorRequirements
    :param debug: True to show debug plots
    :type debug: bool
    :return: calculated requirements and values (from input parameters)
    :rtype: CalculatedRequirementsValues
    """
    new_time_sample_rate = np.linspace(capacitor_requirements.current_waveform_for_op_max_current[0][0],
                                       capacitor_requirements.current_waveform_for_op_max_current[0][-1], 5000)
    new_current_sample_rate = np.interp(new_time_sample_rate, capacitor_requirements.current_waveform_for_op_max_current[0],
                                        capacitor_requirements.current_waveform_for_op_max_current[1])

    # experimentally figure out c_min
    c_min = 1e-9
    c_max = 1e3
    for _ in np.linspace(1, 50, 50):
        charge = integrate(new_time_sample_rate, new_current_sample_rate)
        v_c_at_c_max = charge / c_max
        v_c_at_c_min = charge / c_min
        # this is the logarithmic mid between c_min and c_max
        c_mid = np.sqrt(c_min * c_max)
        v_c_at_c_mid = charge / c_mid

        v_ripple_at_c_mid = np.max(v_c_at_c_mid) - np.min(v_c_at_c_mid)

        if v_ripple_at_c_mid > capacitor_requirements.maximum_peak_to_peak_voltage_ripple:
            c_min = c_mid
        else:
            c_max = c_mid

    i_rms = np.sqrt(np.mean(capacitor_requirements.current_waveform_for_op_max_current[1] ** 2))

    if debug:
        fig, ax = plt.subplots(nrows=2, ncols=1)
        ax[0].plot(new_time_sample_rate, new_current_sample_rate)
        ax[1].plot(new_time_sample_rate, v_c_at_c_max, label="c_max")
        ax[1].plot(new_time_sample_rate, v_c_at_c_min, label="c_min")
        ax[1].plot(new_time_sample_rate, v_c_at_c_mid, label="c_mid")

        ax[0].grid()
        ax[1].grid()
        plt.legend()
        plt.show()

    return CalculatedRequirementsValues(
        requirement_c_min=c_mid,
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
        derating_factor = 1
    elif ambient_temperature > df_derating["temperature"][-1]:
        derating_factor = 0
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
    thermal_coefficient_series = df["g_in_W_degreeCelsius"].loc[(df["width_in_m"] == width) & (df["length_in_m"] == length) & (df["height_in_m"] == height)]

    if len(thermal_coefficient_series.values) != 1:
        thermal_coefficient = np.nan
        logger.info("Value can not be found in the thermal coefficient database. Something must be wrong with the table data.\n"
                    f"{width=}, {height=}, {length=}")
    else:
        thermal_coefficient = float(thermal_coefficient_series.values[0])

    return float(thermal_coefficient)

def select_capacitors(c_requirements: CapacitorRequirements) -> tuple[list[str], list[pd.DataFrame]]:
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

    capacitor_df_list = []

    [frequency_list, current_amplitude_list, _] = fft(c_requirements.current_waveform_for_op_max_current, plot='no',
                                                      mode='time', title='ffT input current')

    path = pathlib.Path(__file__)
    capacitor_series_values_path = pathlib.PurePath(path.parents[0], f"{const.FOIL_CAPACITOR_SERIES_VALUES}.csv")
    series_values = pd.read_csv(capacitor_series_values_path, delimiter=';', decimal=',')

    for capacitor_series_name in const.FOIL_CAPACITOR_SERIES_NAME_LIST:

        # select all suitable capacitors including derating and thermal information from the database
        c_db, c_thermal, c_derating, lt_dto_list = load_dc_film_capacitors(capacitor_series_name)

        derating_factor = get_temperature_current_derating_factor(ambient_temperature=c_requirements.temperature_ambient, df_derating=c_derating)

        # check for temperature derating depending on the capacitor series
        delta_t_jc_max = series_values.loc[series_values["series"] == capacitor_series_name, "delta_t_jc"].values[0]
        delta_temperature_max = derating_factor ** 2 * delta_t_jc_max

        # The interpolation is made at the given datasheet temperatures of 85 °C, 105 °C and 125 °C. This is same for all capacitors in the database.
        # the voltage rating is for t_op = t_ambient + delta_t_self_heating (see datasheet).
        # This is the reason to estimate the maximum inner allowed operating temperature
        virtual_inner_max_temperature = c_requirements.temperature_ambient + delta_temperature_max
        c_db['V_op_max_virt'] = c_db.apply(
            lambda x, v_i_t=virtual_inner_max_temperature:
            np.interp(v_i_t, [const.TEMPERATURE_85, const.TEMPERATURE_105, const.TEMPERATURE_125],
                      [x["V_R_85degree"], x["V_op_105degree"], x["V_op_125degree"]]), axis=1)

        # voltage: calculate the number of needed capacitors in a series connection
        # the voltage rating is for t_op = t_ambient + delta_t_self_heating (see datasheet)
        c_db["in_series_needed"] = np.ceil(c_requirements.v_dc_for_op_max_voltage / (c_db['V_op_max_virt'] * \
                                                                                     (1 + c_requirements.voltage_safety_margin_percentage / 100)))
        # drop series connection capacitors more than specified
        c_db = c_db.drop(c_db[c_db["in_series_needed"] > c_requirements.maximum_number_series_capacitors].index)

        # capacitance: calculate the number of parallel capacitors needed to meet the capacitance requirement
        c_db["in_parallel_needed"] = np.ceil(
            calculated_boundaries.requirement_c_min / (c_db["capacitance"] * (1 - c_requirements.capacitor_tolerance_percent / 100) / c_db["in_series_needed"]))

        # current: calculate the number of parallel capacitors needed to meet the current requirement
        c_db["parallel_current_capacitors_needed"] = c_db.apply(lambda x, der_f=derating_factor: current_capability_film_capacitor(
            order_number=x["ordering code"], frequency_list=frequency_list, current_amplitude_list=current_amplitude_list, derating_factor=der_f),
            axis=1)

        index_ripple_current = c_db["parallel_current_capacitors_needed"] > c_db["in_parallel_needed"]
        c_db.loc[index_ripple_current, "in_parallel_needed"] = c_db.loc[index_ripple_current, "parallel_current_capacitors_needed"]
        c_db = c_db.drop(columns=["parallel_current_capacitors_needed"])

        # volume calculation
        c_db["volume_total"] = c_db["in_parallel_needed"] * c_db["in_series_needed"] * c_db["volume"]

        # filter by resonance frequency: drop capacitors with resonance frequency lower than the current 1st harmonic frequency.
        # ESL_total = L * n_serial / n_parallel
        # C_total = C * n_parallel / n_serial
        # ESL_total * C_total = L * C !!! To estimate the resonance frequency, it does not matter how the series and parallel connection is.
        c_db["f_res"] = 1 / (2 * np.pi * np.sqrt(c_db["capacitance"] * c_db["ESL_in_H"]))
        c_db = c_db.drop(c_db[c_db["f_res"] < frequency_list[0]].index)

        # loss calculation per capacitor
        c_db["power_loss_per_capacitor"] = c_db.apply(lambda x: power_loss_film_capacitor(x["ordering code"], frequency_list, current_amplitude_list,
                                                                                          x["in_parallel_needed"]), axis=1)
        # loss calculation for all capacitors
        c_db.loc[:, 'power_loss_total'] = c_db.loc[:, 'power_loss_per_capacitor'] * c_db["in_parallel_needed"] * c_db["in_series_needed"]

        # self heating calculation
        # g_in_W_degreeCelsius is the equivalent heat coefficient according to the data sheet
        c_db['g_in_W_degreeCelsius'] = c_db.apply(lambda x, c_th=c_thermal: get_equivalent_heat_coefficient(
            c_th, x["width_in_m"], x["length_in_m"], x["height_in_m"]), axis=1)
        c_db = c_db.drop(c_db[np.isnan(c_db["g_in_W_degreeCelsius"])].index)
        c_db["delta_temperature"] = c_db['power_loss_total'] / c_db['g_in_W_degreeCelsius']

        # drop too high self-heated capacitors
        c_db = c_db.drop(c_db[c_db["delta_temperature"] > delta_temperature_max].index)

        # calculate component cost according to cost models
        c_db["cost"] = c_db["in_parallel_needed"] * c_db["in_series_needed"] * \
            c_db.apply(lambda x: cost.cost_film_capacitor(x["V_R_85degree"], x["capacitance"]), axis=1)

        c_db.to_csv(f"results_{capacitor_series_name}.csv")

        capacitor_df_list.append(c_db)

    return const.FOIL_CAPACITOR_SERIES_NAME_LIST, capacitor_df_list
