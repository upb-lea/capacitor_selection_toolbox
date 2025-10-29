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
    maximum_number_series_capacitors=2,
    capacitor_tolerance=cst.CapacitanceTolerance.TenPercent
)

# capacitor pareto plane calculation
c_db = cst.select_capacitors(capacitor_requirements)

# plot capacitor pareto plane
cst.global_plot_settings_font_latex()
fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(80/25.4, 80/25.4))
ax.scatter(c_db["volume_total"] * cst.QUBIC_METER_TO_QUBIC_DECIMETER, c_db["power_loss_total"] * cst.NORM_TO_MILLI, color="black")
ax.set_xlabel("Total capacitor bank volume / dm³")
ax.set_ylabel("Total capacitor bank losses / mW")
ax.grid()
ax.set_xlim(100, 600)
ax.set_ylim(0, 4)
plt.tight_layout()
fig.savefig("pareto_capacitor.pdf")
plt.show()
