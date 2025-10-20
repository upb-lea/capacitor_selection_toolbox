"""Misc calcualtions."""

# 3rd party libraries
import numpy as np

# own libraries
from cst.cst_dataclasses import SelectCapacitor, CalculatedRequirementsValues

def calculate_from_requirements(capacitor_requirements: SelectCapacitor) -> CalculatedRequirementsValues:
    """
    Values and requirements for further calculations needed from the input values.

    :param capacitor_requirements: capacitor requirements and input values in a DTO
    :type capacitor_requirements: SelectCapacitor
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
