"""Capacitor selection toolbox dataclasses."""

# python libraries
from dataclasses import dataclass
from enum import IntEnum

# 3rd party libraries
import numpy as np
import pandas as pd

class CapacitorType(IntEnum):
    """Enum for the capacitor type."""

    FilmCapacitor = 0
    ElectrolyticCapacitor = 1

class CapacitanceTolerance(IntEnum):
    """Typical capacitance tolerance values as enum."""

    TenPercent = 10
    FivePercent = 5


@dataclass
class CapacitorRequirements:
    """Input values and boundaries for the capacitor selection."""

    maximum_peak_to_peak_voltage_ripple: float
    current_waveform_for_op_max_current: np.ndarray
    v_dc_for_op_max_current: float
    current_waveform_for_op_max_voltage: np.ndarray
    v_dc_for_op_max_voltage: float
    temperature_ambient: float
    voltage_safety_margin_percentage: float
    capacitor_type_list: list[CapacitorType]
    maximum_number_series_capacitors: int
    capacitor_tolerance_percent: CapacitanceTolerance

@dataclass
class CalculatedRequirementsValues:
    """From input values calculated values or requirements."""

    requirement_c_min: float
    i_rms: float

@dataclass
class LifetimeDerating:
    """Class to handle capacitor lifetime derating."""

    voltage: float
    temperature: float
    lifetime: pd.DataFrame
