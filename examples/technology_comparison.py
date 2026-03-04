"""Capacitor selection example."""
# python libraries
import logging
import os.path

# 3rd party libraries
import numpy as np
from matplotlib import pyplot as plt

# own libraries
import pecst

logger = logging.getLogger(__name__)
hdlr = logging.StreamHandler()
fhdlr = logging.FileHandler("log_file.log")
logger.addHandler(hdlr)
logger.addHandler(fhdlr)
logger.setLevel(logging.DEBUG)

# capacitor requirements
capacitor_requirements = pecst.CapacitorRequirements(
    maximum_peak_to_peak_voltage_ripple=1,
    current_waveform_for_op_max_current=np.array([[0, 1.25e-6, 2.5e-6, 3.75e-6, 5e-6], [18, 25, -18, -25, 18]]),
    v_dc_for_op_max_voltage=600,
    temperature_ambient=60,
    voltage_safety_margin_percentage=10,
    # capacitor_type_list=[pecst.CapacitorType.FilmCapacitor, pecst.CapacitorType.CeramicCapacitor, pecst.CapacitorType.ElectrolyticCapacitor],
    capacitor_type_list=[pecst.CapacitorType.FilmCapacitor, pecst.CapacitorType.ElectrolyticCapacitor],
    maximum_number_series_capacitors=8,
    capacitor_tolerance_percent=pecst.CapacitanceTolerance.TenPercent,
    lifetime_h=30_000,
    results_directory=os.path.dirname(os.path.abspath(__file__))
)

# capacitor pareto plane calculation
c_name_list, c_db_list = pecst.select_capacitors(capacitor_requirements)
color_list = [pecst.gnome_colors["black"], pecst.gnome_colors["red"], pecst.gnome_colors["blue"]]

# plot capacitor pareto plane
pecst.global_plot_settings_font_latex()
pecst.update_font_size(8)
fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(80/25.4, 60/25.4), sharey=True)
for count, c_db in enumerate(c_db_list):
    ax[0].scatter(c_db["volume_total"] * pecst.QUBIC_METER_TO_QUBIC_DECI_METER, c_db["power_loss_total"], color=color_list[count], label=c_name_list[count])
    ax[1].scatter(c_db["area_total"] * pecst.SQUARE_METER_TO_SQUARE_CENTI_METER, c_db["power_loss_total"], color=color_list[count], label=c_name_list[count])

ax[0].set_xlabel(r"Total capacitor volume $V_\mathrm{C,total}$ / dm³")
ax[0].set_ylabel(r"Total capacitor loss $P_\mathrm{loss,total}$ / W")
ax[0].grid()
# ax.set_xlim(100, 600)
# ax.set_ylim(0, 4)
ax[0].legend()

ax[1].set_xlabel(r"Total capacitor area $A_\mathrm{C,total}$ / cm²")
ax[1].set_ylabel(r"Total capacitor loss $P_\mathrm{loss,total}$ / W")
ax[1].grid()
ax[1].legend()
plt.tight_layout()
# fig.savefig("technology_comparison.pdf")
plt.show()
