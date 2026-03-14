"""Misc calculations."""
# python libraries
import logging
import os.path
import pathlib

# 3rd party libraries
import numpy as np
import pandas as pd

# own libraries
from pecst.cst_dataclasses import CapacitorRequirements
from pecst.functions import fft, calculate_from_requirements
from pecst.film.read_capacitor_database import load_dc_film_capacitors
from pecst.film.power_loss import power_loss_film_capacitor
import pecst.constants as const
import pecst.cost_models as cost
from pecst.film.current_capability import current_capability_film_capacitor
from pecst.film.lifetime import voltage_rating_due_to_lifetime
from pecst.film.dvdt import calc_parallel_capacitors_dvdt

logger = logging.getLogger(__name__)

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
    elif ambient_temperature > df_derating["temperature"].iloc[-1]:
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
        logger.debug("Value can not be found in the thermal coefficient database. Something must be wrong with the table data.\n"
                     f"{width=}, {height=}, {length=}")
    else:
        thermal_coefficient = float(thermal_coefficient_series.values[0])

    return float(thermal_coefficient)

def select_film_capacitors(c_requirements: CapacitorRequirements) -> tuple[list[str], list[pd.DataFrame]]:
    """
    Select suitable film capacitors for the given application.

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
    logger.info("Calculate requirements and values from given input data.")
    calculated_boundaries = calculate_from_requirements(c_requirements)

    capacitor_df_list = []

    logger.info("FFT")
    [frequency_list, current_amplitude_list, _] = fft(c_requirements.current_waveform_for_op_max_current, plot='no',
                                                      mode='time', title='ffT input current')

    path = pathlib.Path(__file__)
    capacitor_series_values_path = pathlib.PurePath(path.parents[1], const.FILM_CAPACITOR_DATA_DIRECTORY, f"{const.FILM_CAPACITOR_SERIES_VALUES}.csv")
    series_values = pd.read_csv(capacitor_series_values_path, delimiter=';', decimal=',')

    for capacitor_series_name in const.FILM_CAPACITOR_SERIES_NAME_LIST:
        logger.info(f"Capacitor series: {capacitor_series_name}")

        # select all suitable capacitors including derating and thermal information from the database
        logger.debug("Load capacitor csv data from disk.")
        c_db, c_thermal, c_derating, dvdt_df, lt_dto_list = load_dc_film_capacitors(capacitor_series_name)

        logger.debug("Get derating curve.")
        derating_factor = get_temperature_current_derating_factor(ambient_temperature=c_requirements.temperature_ambient, df_derating=c_derating)

        # check for temperature derating depending on the capacitor series
        delta_t_jc_max = series_values.loc[series_values["series"] == capacitor_series_name, "delta_t_jc"].values[0]
        delta_temperature_max = derating_factor ** 2 * delta_t_jc_max

        # The interpolation is made at the given datasheet temperatures of 85 °C, 105 °C and 125 °C. This is same for all capacitors in the database.
        # the voltage rating is for t_op = t_ambient + delta_t_self_heating (see datasheet).
        # This is the reason to estimate the maximum inner allowed operating temperature
        logger.debug("Calculate virtual inner temperature.")
        virtual_inner_max_temperature = c_requirements.temperature_ambient + delta_temperature_max
        c_db['V_op_max_virt'] = c_db.apply(
            lambda x, v_i_t=virtual_inner_max_temperature:
            np.interp(v_i_t, [const.TEMPERATURE_85, const.TEMPERATURE_105, const.TEMPERATURE_125],
                      [x["V_R_85degree"], x["V_op_105degree"], x["V_op_125degree"]]), axis=1)

        # voltage lifetime_h derating
        logger.debug("Lifetime derating.")
        logger.debug(f"{virtual_inner_max_temperature=}")
        c_db["voltage_lifetime"] = c_db.apply(lambda x, v_i_t=virtual_inner_max_temperature, lt_dto_list=lt_dto_list: voltage_rating_due_to_lifetime(
            target_lifetime=c_requirements.lifetime_h, operating_temperature=float(v_i_t),
            voltage_rating=x["V_R_85degree"], lt_dto_list=lt_dto_list), axis=1)

        c_db = c_db.drop(c_db[pd.isnull(c_db["voltage_lifetime"])].index)

        c_db["factor_lifetime"] = c_db["voltage_lifetime"] / c_db["V_R_85degree"]

        # voltage: calculate the number of needed capacitors in a series connection
        # the voltage rating is for t_op = t_ambient + delta_t_self_heating (see datasheet)
        logger.debug("Calculate in series needed capacitors.")
        c_db["in_series_needed"] = np.ceil(c_requirements.v_dc_for_op_max_voltage / (c_db['V_op_max_virt'] * c_db["factor_lifetime"] * \
                                                                                     (1 - c_requirements.voltage_safety_margin_percentage / 100)))
        # drop series connection capacitors more than specified
        c_db = c_db.drop(c_db[c_db["in_series_needed"] > c_requirements.maximum_number_series_capacitors].index)

        if len(c_db["capacitance"]) == 0:
            # all capacitors are sorted out due to lifetime ratings. Add empty keys
            c_db["volume_total"] = np.nan
            c_db["power_loss_total"] = np.nan
        else:
            # capacitance: calculate the number of parallel capacitors needed to meet the capacitance requirement
            logger.debug("Calculate in parallel needed capacitors due to capacitance.")
            c_db["in_parallel_needed"] = np.ceil(
                calculated_boundaries.requirement_c_min / (c_db["capacitance"] * \
                                                           (1 - c_requirements.capacitor_tolerance_percent / 100) / c_db["in_series_needed"]))

            # dv/dt: calculate the number of parallel capacitors needed to meet the dv/dt requirement
            logger.debug("Calculate in parallel needed capacitors due to dv/dt limit.")
            c_db["in_parallel_needed_dvdt"] = c_db.apply(lambda x, dvdt_df=dvdt_df, i_peak=calculated_boundaries.i_max: calc_parallel_capacitors_dvdt(
                x["capacitance"], x["V_R_85degree"], i_peak, dvdt_df, x["ordering code"], calculated_boundaries), axis=1)

            # current: calculate the number of parallel capacitors needed to meet the current requirement
            logger.debug("Calculate in parallel needed capacitors due to current limitation over frequency.")
            c_db["parallel_current_capacitors_needed"] = c_db.apply(lambda x, der_f=derating_factor: current_capability_film_capacitor(
                order_number=x["ordering code"], frequency_list=frequency_list, current_amplitude_list=current_amplitude_list, derating_factor=der_f),
                axis=1)

            # check if parallel capacitors due to current needed is more than due to capacitance needed
            index_dvdt = c_db["in_parallel_needed_dvdt"] > c_db["in_parallel_needed"]
            c_db.loc[index_dvdt, "in_parallel_needed"] = c_db.loc[index_dvdt, "in_parallel_needed_dvdt"]

            # check if parallel capacitors due to current needed is more than due to capacitance needed
            index_ripple_current = c_db["parallel_current_capacitors_needed"] > c_db["in_parallel_needed"]
            c_db.loc[index_ripple_current, "in_parallel_needed"] = c_db.loc[index_ripple_current, "parallel_current_capacitors_needed"]
            c_db = c_db.drop(columns=["parallel_current_capacitors_needed", "in_parallel_needed_dvdt"])

            # volume calculation
            logger.debug("Volume calculation.")
            c_db["volume_total"] = c_db["in_parallel_needed"] * c_db["in_series_needed"] * c_db["volume"]

            # filter by resonance frequency: drop capacitors with resonance frequency lower than the current 1st harmonic frequency.
            # ESL_total = L * n_serial / n_parallel
            # C_total = C * n_parallel / n_serial
            # ESL_total * C_total = L * C !!! To estimate the resonance frequency, it does not matter how the series and parallel connection is.
            logger.debug("Resonance frequency filtering.")
            c_db["f_res"] = 1 / (2 * np.pi * np.sqrt(c_db["capacitance"] * c_db["ESL_in_H"]))
            c_db = c_db.drop(c_db[c_db["f_res"] < frequency_list[0]].index)

            # loss calculation per capacitor
            logger.debug("Power loss estimation by ESR.")
            c_db["power_loss_per_capacitor"] = c_db.apply(lambda x: power_loss_film_capacitor(x["ordering code"], frequency_list, current_amplitude_list,
                                                                                              x["in_parallel_needed"]), axis=1)
            # loss calculation for all capacitors
            c_db.loc[:, 'power_loss_total'] = c_db.loc[:, 'power_loss_per_capacitor'] * c_db["in_parallel_needed"] * c_db["in_series_needed"]

            # self heating calculation
            # g_in_W_degreeCelsius is the equivalent heat coefficient according to the data sheet
            logger.debug("Self heating.")
            c_db['g_in_W_degreeCelsius'] = c_db.apply(lambda x, c_th=c_thermal: get_equivalent_heat_coefficient(
                c_th, x["width_in_m"], x["length_in_m"], x["height_in_m"]), axis=1)
            c_db = c_db.drop(c_db[np.isnan(c_db["g_in_W_degreeCelsius"])].index)
            c_db["delta_temperature"] = c_db['power_loss_total'] / c_db['g_in_W_degreeCelsius']

            # drop too high self-heated capacitors
            c_db = c_db.drop(c_db[c_db["delta_temperature"] > delta_temperature_max].index)

            # calculate component cost according to cost models
            logger.debug("Calculate component cost.")
            c_db["cost"] = c_db["in_parallel_needed"] * c_db["in_series_needed"] * \
                c_db.apply(lambda x: cost.cost_film_capacitor(x["V_R_85degree"], x["capacitance"]), axis=1)

            # calculate minimum required PCB area
            c_db["area_total"] = c_db["area"] * c_db["in_parallel_needed"] * c_db["in_series_needed"]

        if not os.path.exists(c_requirements.results_directory):
            os.makedirs(c_requirements.results_directory)

        logger.debug(f"Save results_film_{capacitor_series_name}.csv")
        c_db.to_csv(f"{c_requirements.results_directory}/results_film_{capacitor_series_name}.csv")

        capacitor_df_list.append(c_db)

    return const.FILM_CAPACITOR_SERIES_NAME_LIST, capacitor_df_list
