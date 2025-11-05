"""Capacitor selection toolbox helper functions."""

# python libraries
import logging

# 3rd party libraries
import numpy as np
from matplotlib import pyplot as plt

logger = logging.getLogger(__name__)

def fft(period_vector_t_i: np.ndarray, sample_factor: int = 1000, plot: str = 'no', mode: str = 'rad',
        f0: float | None = None, title: str = 'ffT', filter_type: str = 'factor',
        filter_value_factor: float = 0.01, filter_value_harmonic: int = 100,
        figure_size: tuple | None = None, figure_directory: str | None = None) -> np.ndarray:
    """
    Calculate the FFT for a given input signal. Input signal is in vector format and should include one period.

    Output vector includes only frequencies with amplitudes > 1% of input signal

    :Minimal Example:

    >>> import numpy as np
    >>> example_waveform = np.array([[0, 1.34, 3.14, 4.48, 6.28],[-175.69, 103.47, 175.69, -103.47,-175.69]])
    >>> out = fft(example_waveform, plot='yes', mode='rad', f0=25000, title='ffT input current')

    :param period_vector_t_i: numpy-array [[time-vector[,[current-vector]]. One period only
    :type period_vector_t_i: np.array
    :param sample_factor: f_sampling/f_period, defaults to 1000
    :type sample_factor: int
    :param plot: insert anything else than "no" or 'False' to show a plot to visualize input and output
    :type plot: str
    :param mode: 'rad'[default]: full period is 2*pi, 'deg': full period is 360°, 'time': time domain.
    :type mode: str
    :param f0: fundamental frequency. Needs to be set in 'rad'- or 'deg'-mode
    :type f0: float
    :param title: plot window title, defaults to 'ffT'
    :type title: str
    :param filter_type: 'factor'[default] or 'harmonic' or 'disabled'.
    :type filter_type: str
    :param filter_value_factor: filters out amplitude-values below a certain factor of max. input amplitude.
        Should be 0...1, default to 0.01 (1%)
    :type filter_value_factor: float
    :param filter_value_harmonic: filters out harmonics up to a certain number. Default value is 100.
        Note: count 1 is DC component, count 2 is the fundamental frequency
    :type filter_value_harmonic: int
    :param figure_directory: full path with file extension
    :type figure_directory: tuple
    :param figure_size: None for auto-fit; fig_size for matplotlib (width, length)
    :type figure_size: tuple

    :return: numpy-array [[frequency-vector],[amplitude-vector],[phase-vector]]
    :rtype: np.ndarray[list]
    """
    # check for correct input parameter
    if (mode == 'rad' or mode == 'deg') and f0 is None:
        raise ValueError("if mode is 'rad' or 'deg', a fundamental frequency f0 must be set")
    # check for input is list. Convert to numpy-array
    if isinstance(period_vector_t_i, list):
        if plot != 'no' and plot is not False:
            logger.warning("Input is list, convert to np.array()")
        period_vector_t_i = np.array(period_vector_t_i)

    # first value of time vector must be zero
    if period_vector_t_i[0][0] != 0:
        raise ValueError("Period vector must start with 0 seconds!")

    # mode pre-calculation
    if f0:
        if mode == 'rad':
            period_vector_t_i[0] = period_vector_t_i[0] / (2 * np.pi * f0)
        elif mode == 'deg':
            period_vector_t_i[0] = period_vector_t_i[0] / (360 * f0)
    if mode != 'time':
        raise ValueError("Mode not available. Choose: 'rad', 'deg', 'time'")

    t = period_vector_t_i[0]
    i = period_vector_t_i[1]

    # fft-function works per default in time domain
    t_interp = np.linspace(0, t[-1], sample_factor)
    i_interp = np.interp(t_interp, t, i)

    f0 = round(1 / t[-1])
    Fs = f0 * sample_factor

    # frequency domain
    f = np.linspace(0, (sample_factor - 1) * f0, sample_factor)
    x = np.fft.fft(i_interp)
    x_mag = np.abs(x) / sample_factor
    phi_rad = np.angle(x)

    f_corrected = f[0:int(sample_factor / 2 + 1)]
    x_mag_corrected = 2 * x_mag[0:int(sample_factor / 2 + 1)]
    x_mag_corrected[0] = x_mag_corrected[0] / 2
    phi_rad_corrected = phi_rad[0:int(sample_factor / 2 + 1)]

    f_out = np.array([])
    x_out = np.array([])
    phi_rad_out = np.array([])
    if filter_type.lower() == 'factor':
        for count, _ in enumerate(x_mag_corrected):
            if x_mag_corrected[count] > filter_value_factor * max(abs(i)):
                f_out = np.append(f_out, f_corrected[count])
                x_out = np.append(x_out, x_mag_corrected[count])
                phi_rad_out = np.append(phi_rad_out, phi_rad_corrected[count])
    elif filter_type.lower() == 'harmonic':
        for count, _ in enumerate(x_mag_corrected):
            if count < filter_value_harmonic:
                f_out = np.append(f_out, f_corrected[count])
                x_out = np.append(x_out, x_mag_corrected[count])
                phi_rad_out = np.append(phi_rad_out, phi_rad_corrected[count])
    elif filter_type.lower() == 'disabled':
        f_out = f_corrected
        x_out = x_mag_corrected
        phi_rad_out = phi_rad_corrected
    else:
        raise ValueError(
            f"filter_type '{filter_value_harmonic}' not available: Must be 'factor','harmonic' or 'disabled ")

    if plot != 'no' and plot is not False:
        logger.info(f"{title=}")
        logger.info(f"{t[-1]=}")
        logger.info(f"{f0=}")
        logger.info(f"{Fs=}")
        logger.info(f"{sample_factor=}")
        logger.info(f"f_out = {np.around(f_out, decimals=0)}")
        logger.info(f"x_out = {np.around(x_out, decimals=3)}")
        logger.info(f"phi_rad_out = {np.around(phi_rad_out, decimals=3)}")

        reconstructed_signal = 0
        for i_range in range(len(f_out)):
            reconstructed_signal += x_out[i_range] * np.cos(
                2 * np.pi * f_out[i_range] * t_interp + phi_rad_out[i_range])

        fig, [ax1, ax2, ax3] = plt.subplots(num=title, nrows=3, ncols=1, figsize=figure_size)
        ax1.plot(t, i, label='original signal')
        ax1.plot(t_interp, reconstructed_signal, label='reconstructed signal')
        ax1.grid()
        ax1.set_title('Signal')
        ax1.set_xlabel('time in s')
        ax1.set_ylabel('Amplitude')
        ax1.legend()
        ax2.stem(f_out, x_out)
        ax2.grid()
        ax2.set_title('ffT')
        ax2.set_xlabel('Frequency in Hz')
        ax2.set_ylabel('Amplitude')

        ax3.stem(f_out, phi_rad_out)
        ax3.grid()
        ax3.set_title('ffT')
        ax3.set_xlabel('Frequency in Hz')
        ax3.set_ylabel('Phase in rad')

        plt.tight_layout()
        if figure_directory is not None:
            plt.savefig(figure_directory, bbox_inches="tight")
        plt.show()

    return np.array([f_out, x_out, phi_rad_out])
