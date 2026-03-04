

# python libraries
import logging
import os
import pathlib

# 3rd party libraries
import pandas as pd
import numpy as np

# own libraries
import pecst.constants as const
from pecst.functions import fft, calculate_from_requirements
from pecst.cst_dataclasses import CapacitorRequirements
from pecst.electrolytic.read_capacitor_database import load_electrolytic_capacitors
from pecst.cst_dataclasses import CapacitorType, CapacitanceTolerance, LifetimeMultiplier

logger = logging.getLogger(__name__)


def get_useful_lifetime(df: pd.DataFrame, voltage: float) -> float:
    """
    Read the useful lifetime (from data sheet).

    :param df: dataframe with equivalent self-heating coefficient based on the capacitor housing dimensions.
    :type df: pandas.DataFrame
    :param voltage: capacitor voltage
    :type voltage: float
    :return: useful lifetime in hours
    :rtype: float
    """
    lifetime_h = df["lifetime_85degree_h"].loc[(df["u_R_V"] == voltage)]

    if len(lifetime_h.values) != 1:
        lifetime_h = np.nan
        logger.debug("Value can not be found in the thermal coefficient database. Something must be wrong with the table data.\n"
                     f"{voltage=}")
    else:
        lifetime_h = float(lifetime_h.values[0])

    return float(lifetime_h)



def neighbors(x, df):
    d = (df["life_multiplier"] - x)
    return df.loc[[d[d == d[d > 0].min()].index[0], d[d == d[d < 0].max()].index[0]]]

def upper_neighbor(x, df):
    d = (df["life_multiplier"] - x)

    try:
        upper_neighbor_df = df.loc[[d[d == d[d > 0].min()].index[0]]]
        return upper_neighbor_df
    except:
        return np.nan


def get_lifetime_current_derating_factor(ambient_temperature: float, target_lifetime: float, useful_lifetime: float, lt_derating_dto_list: list[LifetimeMultiplier]) -> float:
    """


    :param ambient_temperature: ambient temperature in degree Celsius
    :type ambient_temperature: float
    :param df_derating: dataframe with temperature derating information
    :type df_derating: pd.DataFrame
    :return: derating factor
    :rtype: float
    """
    target_lifetime_multiplier = target_lifetime / useful_lifetime
    if target_lifetime_multiplier < 1:
        return np.nan

    # find the nearest lifetime multiplier greater than the target one
    lt_derating_life_multiplier = 100
    minimum_multiplier_difference = 100
    lt_dto = None
    for lt_derating_dto in lt_derating_dto_list:
        multiplier_difference = lt_derating_dto.life_multiplier - target_lifetime_multiplier

        if multiplier_difference >= 0 and multiplier_difference <= minimum_multiplier_difference:
            lt_derating_life_multiplier = lt_derating_dto.life_multiplier
            minimum_multiplier_difference = multiplier_difference
            lt_dto = lt_derating_dto

    if lt_derating_life_multiplier == 100:
        # no higher multiplier has been found
        return np.nan

    current_derating_factor = np.interp(ambient_temperature, lt_dto.current_factor_vs_temperature["temperature"], lt_dto.current_factor_vs_temperature["current_factor"])

    # limit current derating factor below minimum given temperature
    if ambient_temperature < lt_dto.current_factor_vs_temperature["temperature"].min():
        current_derating_factor = lt_dto.current_factor_vs_temperature["current_factor"][0]
    # do not allow designs with a higher ambient temperature then allowed
    elif ambient_temperature > lt_dto.current_factor_vs_temperature["temperature"].max():
        current_derating_factor = np.nan

    return current_derating_factor


def select_electrolytic_capacitors(c_requirements: CapacitorRequirements) -> tuple[list[str], list[pd.DataFrame]]:
    """
    Select suitable electrolytic capacitors for the given application.

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

    for capacitor_series_name in const.ELECTROLYTIC_CAPACITOR_SERIES_NAME_LIST:
        logger.info(f"Capacitor series: {capacitor_series_name}")

        # select all suitable capacitors including derating and thermal information from the database
        logger.debug("Load capacitor csv data from disk.")
        c_db, lt_df, lt_df_factors, esr_vs_temperature_dto_list, c_vs_f_dto_list = load_electrolytic_capacitors(capacitor_series_name)

        # current lifetime_h derating
        logger.debug("Lifetime derating.")
        c_db["nominal_lifetime"] = c_db.apply(lambda x: get_useful_lifetime(lt_df, voltage=x["v_r_V"]), axis=1)

        print(c_db.head())

        # get lifetime derating factor
        c_db["current_derating_factor"] = c_db.apply(lambda x: get_lifetime_current_derating_factor(
            c_requirements.temperature_ambient, c_requirements.lifetime_h, x["nominal_lifetime"], lt_df_factors), axis=1)


        print(c_db.head())



        # voltage: calculate the number of needed capacitors in a series connection
        # the voltage rating is for t_op = t_ambient + delta_t_self_heating (see datasheet)
        logger.debug("Calculate in series needed capacitors.")
        c_db["in_series_needed"] = np.ceil(c_requirements.v_dc_for_op_max_voltage / (c_db['V_op_max_virt'] * c_db["factor_lifetime"] * \
                                                                                     (1 + c_requirements.voltage_safety_margin_percentage / 100)))
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

            # calculate minimum required PCB area
            c_db["area_total"] = c_db["area"] * c_db["in_parallel_needed"] * c_db["in_series_needed"]

        if not os.path.exists(c_requirements.results_directory):
            os.makedirs(c_requirements.results_directory)

        logger.debug(f"Save results_electrolytic_{capacitor_series_name}.csv")
        c_db.to_csv(f"{c_requirements.results_directory}/results_electrolytic_{capacitor_series_name}.csv")

        capacitor_df_list.append(c_db)

    return const.FOIL_CAPACITOR_SERIES_NAME_LIST, capacitor_df_list


if __name__ == "__main__":
    # capacitor requirements
    capacitor_requirements = CapacitorRequirements(
        maximum_peak_to_peak_voltage_ripple=1,
        current_waveform_for_op_max_current=np.array([[0, 1.25e-6, 2.5e-6, 3.75e-6, 5e-6], [18, 25, -18, -25, 18]]),
        v_dc_for_op_max_voltage=600,
        temperature_ambient=60,
        voltage_safety_margin_percentage=10,
        capacitor_type_list=[CapacitorType.ElectrolyticCapacitor],
        maximum_number_series_capacitors=8,
        capacitor_tolerance_percent=CapacitanceTolerance.TenPercent,
        lifetime_h=29_000,
        results_directory=os.path.dirname(os.path.abspath(__file__))
    )

    # capacitor pareto plane calculation
    c_name_list, c_db_list = select_electrolytic_capacitors(capacitor_requirements)