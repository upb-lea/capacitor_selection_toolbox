"""Capacitor selection toolbox dataclasses."""

# python libraries
from dataclasses import dataclass

# 3rd party libraries
import numpy as np

@dataclass
class SelectCapacitor:
    maximum_peak_to_peak_voltage_ripple: float
    current_waveform_operation_point_1: np.ndarray
    v_dc_operating_point_1: float
    current_waveform_operation_point_2: np.ndarray
    v_dc_operating_point_2: float
    temperature_ambient: float
