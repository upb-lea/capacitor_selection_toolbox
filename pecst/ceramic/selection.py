"""Misc calculations."""
# python libraries
import logging
import os
import pathlib

# 3rd party libraries
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

# own libraries
from pecst.cst_dataclasses import CapacitorRequirements
from pecst.functions import fft, calculate_from_requirements
import pecst.constants as const
from pecst.cst_dataclasses import CapacitorType, CapacitanceTolerance
from pecst.ceramic.power_loss import power_loss_ceramic_capacitor
from pecst.ceramic.dc_bias import dc_bias_series_parallel_connection

logger = logging.getLogger(__name__)


def decode_kemet_type_label(type_label: str) -> tuple[float, float, float, float, float]:
    """
    Decode the kemet type label.

    :param type_label: type label / ordering code
    :return:
    """
    def decode_smd_housing_size(housing_size_code: str) -> float:
        area_from_dict = const.SMD_SIZE_DF.loc[housing_size_code == const.SMD_SIZE_DF["size"]]["area"].values[0]
        return float(area_from_dict)

    def decode_smd_footprint_size(housing_size_code: str) -> float:
        footprint_area_from_dict = const.SMD_SIZE_DF.loc[housing_size_code == const.SMD_SIZE_DF["size"]]["footprint_area"].values[0]
        return float(footprint_area_from_dict)

    def decode_capacitance_code(capacitance_code: str) -> float:
        """
        First two digits represent significant figures. Third digit specifies number of zeros to follow. In pF.

        :param capacitance_code: e.g. "102" -> 10 * 10² pF = 1 nF
        :return: capacitance / F, area / m², tolerance, voltage / V
        """
        capacitance = float(capacitance_code[0:2]) * 10 ** float(capacitance_code[-1]) * const.PICO_TO_NORM
        return capacitance

    def decode_voltage_code(voltage_code: str) -> float:
        return const.VOLTAGE_CODE_KEMET_DICT[voltage_code]

    def decode_tolerance_code(tolerance_code: str) -> float:
        return const.CAPACITANCE_TOLERANCE_KEMET_DICT[tolerance_code]

    housing_size_code = type_label[0:5]
    capacitance_code = type_label[6:9]
    tolerance_code = type_label[9]
    voltage_code = type_label[10]
    material_code = type_label[11]

    area = decode_smd_housing_size(housing_size_code)
    footprint_area = decode_smd_footprint_size(housing_size_code)
    capacitance = decode_capacitance_code(capacitance_code)
    tolerance = decode_tolerance_code(tolerance_code)
    voltage = decode_voltage_code(voltage_code)

    return capacitance, area, footprint_area, tolerance, voltage

def select_ceramic_capacitors(c_requirements: CapacitorRequirements) -> tuple[list[str], list[pd.DataFrame]]:
    """
    Select suitable ceramic capacitors for the given application.

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
    """
    # calculate minimum required capacitance and RMS current
    logger.info("Calculate requirements and values from given input data.")
    calculated_boundaries = calculate_from_requirements(c_requirements)

    logger.info("FFT")
    [frequency_list, current_amplitude_list, _] = fft(c_requirements.current_waveform_for_op_max_current, plot='no',
                                                      mode='time', title='ffT input current')

    path = pathlib.Path(__file__)
    capacitor_downloads_path = pathlib.PurePath(path.parents[1], const.CERAMIC_CAPACITOR_DOWNLOAD_DIRECTORY)

    # generate available capacitor dataframe

    filenames = next(os.walk(capacitor_downloads_path), (None, None, []))[2]  # [] if no file
    unique_files = [filename for filename in filenames if "_Imp,ESR.csv" in filename]
    unique_files = [filename.replace("_Imp,ESR.csv", "") for filename in unique_files]

    ceramic_df = pd.DataFrame()

    for type_label in unique_files:
        capacitance, area, footprint_area, tolerance, voltage = decode_kemet_type_label(type_label)

        df = pd.DataFrame({"ordering code": type_label, "capacitance": [capacitance], "voltage": [voltage], "area": area, "footprint_area": footprint_area,
                           "tolerance": tolerance})
        ceramic_df = pd.concat([ceramic_df, df], axis=0)

    # sort out all capacitors where to many series capacitors are required (more than maximum in series allowed)
    ceramic_df["number_min_capacitors_in_series"] = np.ceil(
        c_requirements.v_dc_for_op_max_voltage / (ceramic_df["voltage"] * (1 + c_requirements.voltage_safety_margin_percentage / 100)))
    ceramic_df = ceramic_df.drop(ceramic_df[ceramic_df["number_min_capacitors_in_series"] > c_requirements.maximum_number_series_capacitors].index)

    if len(ceramic_df["capacitance"]) == 0:
        # all capacitors are sorted out due to lifetime ratings. Add empty keys
        ceramic_df["volume_total"] = np.nan
        ceramic_df["power_loss_total"] = np.nan
    else:
        # figure out if the series connection or the parallel connection is the better option (considering dc bias)
        logger.info("Series vs. parallel connection.")
        ceramic_df[["in_series_needed", "in_parallel_needed"]] = ceramic_df.apply(
            lambda x, v_dc_max=c_requirements.v_dc_for_op_max_voltage, n_max_c=c_requirements.maximum_number_series_capacitors,
            c_min_req=calculated_boundaries.requirement_c_min: dc_bias_series_parallel_connection(
                x["ordering code"], x["capacitance"], v_dc_max, x["number_min_capacitors_in_series"], n_max_c, c_min_req), axis=1)

        print(ceramic_df.shape)
        print(ceramic_df.head())
        ceramic_df.to_csv(f"{c_requirements.results_directory}/results_intermediate_ceramic.csv")

        # drop capacitors with no bias curve data given
        print("drop data")
        # ceramic_df = ceramic_df.drop(ceramic_df[np.isnan(ceramic_df["in_series_needed"])].index)

        print("after remove of nans")
        print(ceramic_df.shape)
        print(f"{frequency_list=}")
        print(f"{current_amplitude_list=}")

        # loss calculation per capacitor
        logger.info("Power loss calculation")
        ceramic_df["power_loss_per_capacitor"] = ceramic_df.apply(
            lambda x: power_loss_ceramic_capacitor(x["ordering code"], frequency_list, current_amplitude_list, x["in_parallel_needed"]), axis=1)

        print(ceramic_df.shape)

        # drop capacitors with no ESR curve data given
        # ceramic_df = ceramic_df.drop(ceramic_df[np.isnan(ceramic_df["power_loss_per_capacitor"])].index)

        print("after remove of nans")
        print(ceramic_df.shape)

        # loss calculation for all capacitors
        ceramic_df.loc[:, 'power_loss_total'] = (
            ceramic_df.loc[:, 'power_loss_per_capacitor'] * ceramic_df["in_parallel_needed"] * ceramic_df["in_series_needed"])

        # calculate minimum required PCB area
        logger.info("Area and volume calculation.")
        ceramic_df["area_total"] = ceramic_df["area"] * ceramic_df["in_parallel_needed"] * ceramic_df["in_series_needed"]
        ceramic_df["area_footprint_total"] = ceramic_df["footprint_area"] * ceramic_df["in_parallel_needed"] * ceramic_df["in_series_needed"]

        # calculate total volume
        ceramic_df["volume_total"] = ceramic_df["area_footprint_total"] * 2e-3  # assumption of capacitor height of 2 mm

    if not os.path.exists(c_requirements.results_directory):
        os.makedirs(c_requirements.results_directory)

    logger.debug("Save results_ceramic.csv")
    ceramic_df.to_csv(f"{c_requirements.results_directory}/results_ceramic.csv")

    return ["ceramic"], [ceramic_df]


if __name__ == "__main__":
    # decode_kemet_type_label("C0402C102K1GAC")

    # capacitor requirements
    capacitor_requirements = CapacitorRequirements(
        maximum_peak_to_peak_voltage_ripple=1,
        current_waveform_for_op_max_current=np.array([[0, 1.25e-6, 2.5e-6, 3.75e-6, 5e-6], [18, 25, -18, -25, 18]]),
        v_dc_for_op_max_voltage=70,
        temperature_ambient=90,
        voltage_safety_margin_percentage=10,
        capacitor_type_list=[CapacitorType.FilmCapacitor],
        maximum_number_series_capacitors=2,
        capacitor_tolerance_percent=CapacitanceTolerance.TenPercent,
        lifetime_h=30_000,
        results_directory=os.path.dirname(os.path.abspath(__file__))
    )

    [name], [df] = select_ceramic_capacitors(capacitor_requirements)
    print(df)

    plt.scatter(df["volume_total"], df["power_loss_total"], c="black")
    plt.show()
