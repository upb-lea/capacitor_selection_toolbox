.. sectnum::

Power Electronics Capacitor Selection Toolbox (PE-CST)
=========================================================================
Toolbox to select suitable foil capacitors for power electronics applications.


Installation
---------------------------------------

::

    pip install pecst


Documentation
---------------------------------------
Capacitor input parameters:
 * ``maximum_peak_to_peak_voltage_ripple``
 * ``current_waveform_for_op_max_current``
 * ``v_dc_for_op_max_current``
 * ``temperature_ambient``
 * ``voltage_safety_margin_percentage``
 * ``capacitor_type_list=[cst.CapacitorType.FilmCapacitor]``
 * ``maximum_number_series_capacitors``
 * ``capacitor_tolerance_percent``
 * ``lifetime_h``


Features:
 * calculating capacitors in series needed considering ``lifetime``, ``voltage_safety_margin_percentage`` and ``temperautre_ambient`` according to datasheet curves
 * calculating capacitors in parallel needed considering minimum required capacitance according to the given current waveform and ``maximum_peak_to_peak_voltage_ripple``
 * calculating capacitors in parallel needed considering maximum ``dv/dt`` per capacitor according to datasheet curves
 * calculating capacitors in parallel needed considering the maximum current ratings per frequency (FFT) according to datasheet curves
 * power loss calculation according to FFT current waveform with frequency-dependent ESR according to datasheet curves
 * temperature rise calculation according to power loss and the capacitors thermal resistance according to datasheet curves
 * volume calculation of the final setup
 * calculating component cost regarding component cost models
 * sort out non-working designs

Output:
 * Performance space values: ``volume``, ``power loss``, ``cost``

Quick start
---------------------------------------

 * run the `automated download of ESR files <https://github.com/upb-lea/capacitor_selection_toolbox/blob/main/examples/download_esr_files.py>`_.
 * run the `Example capacitor selection file <https://github.com/upb-lea/capacitor_selection_toolbox/blob/main/examples/capacitor_selection_example.py>`_.