"""Capacitor selection toolbox dataclasses."""

# python libraries
from dataclasses import dataclass
from enum import IntEnum

# 3rd party libraries
import numpy as np

class CapacitorType(IntEnum):
    FilmCapacitor = 0
    ElectrolyticCapacitor = 1

@dataclass
class SelectCapacitor:
    maximum_peak_to_peak_voltage_ripple: float
    current_waveform_for_op_max_current: np.ndarray
    v_dc_for_op_max_current: float
    current_waveform_for_op_max_voltage: np.ndarray
    v_dc_for_op_max_voltage: float
    temperature_ambient: float
    voltage_safety_margin_percentage: float
    capacitor_type_list: list[CapacitorType]
    maximum_number_series_capacitors: int

@dataclass
class CalculatedRequirementsValues:
    requirement_c_min: float
    i_rms: float
