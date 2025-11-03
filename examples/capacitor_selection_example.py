"""Capacitor selection example."""
# python libraries
import logging

# 3rd party libraries
import numpy as np
from matplotlib import pyplot as plt

# own libraries
import cst

# configure logging to show femmt terminal output
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

# capacitor requirements
capacitor_requirements = cst.CapacitorRequirements(
    maximum_peak_to_peak_voltage_ripple=1,
    current_waveform_for_op_max_current=np.array([[0, 1.25e-6, 2.5e-6, 3.75e-6, 5e-6], [18, 25, -18, -25, 18]]),
    v_dc_for_op_max_current=700,
    current_waveform_for_op_max_voltage=np.array([[0, 1.25e-6, 2.5e-6, 3.75e-6, 5e-6], [8, 19, -8, -9, 8]]),
    v_dc_for_op_max_voltage=730,
    temperature_ambient=90,
    voltage_safety_margin_percentage=10,
    capacitor_type_list=[cst.CapacitorType.FilmCapacitor],
    maximum_number_series_capacitors=2,
    capacitor_tolerance_percent=cst.CapacitanceTolerance.TenPercent,
    lifetime_h=300_000
)

# capacitor pareto plane calculation
c_name_list, c_db_list = cst.select_capacitors(capacitor_requirements)
color_list = [cst.gnome_colors["black"], cst.gnome_colors["red"], cst.gnome_colors["blue"]]

# plot capacitor pareto plane
cst.global_plot_settings_font_latex()
cst.update_font_size(8)
fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(80/25.4, 60/25.4))
for count, c_db in enumerate(c_db_list):
    ax.scatter(c_db["volume_total"] * cst.QUBIC_METER_TO_QUBIC_DECI_METER, c_db["power_loss_total"],
               color=color_list[count], label=c_name_list[count])
ax.set_xlabel(r"$V_\mathrm{C,total}$ / dm³")
ax.set_ylabel(r"$P_\mathrm{loss,total}$ / W")
ax.grid()
# ax.set_xlim(100, 600)
# ax.set_ylim(0, 4)
ax.legend()
plt.tight_layout()
fig.savefig("pareto_capacitor.pdf")
plt.show()
