"""Capacitor selection example."""

# 3rd party libraries
import numpy as np
from matplotlib import pyplot as plt

# own libraries
import cst

# capacitor requirements
capacitor_requirements = cst.CapacitorRequirements(
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

# capacitor pareto plane calculation
c_db = cst.select_capacitors(capacitor_requirements)

# plot capacitor pareto plane
plt.scatter(c_db["volume_total"] * cst.QUBIC_METER_TO_QUBIC_DECIMETER, c_db["power_loss_total"])
plt.xlabel("Total capacitor volume / dm³")
plt.ylabel("total capacitor loss / W")
plt.grid()
plt.show()
