"""
This file contains functions for standalone IV measurements
"""

import warnings
import numpy as np
import silab_collections.meas as meas
import silab_collections.meas.smu as smu_utils
from silab_collections.meas.data_writer import DataWriter
from basil.dut import Dut
from tqdm import tqdm
from time import time, sleep, strftime


def _measure_and_write_current(smu, n_meas, bias, writer, pbar, log):

    # We only take one measurement
    if n_meas == 1:
        current = smu_utils.get_current_reading(smu=smu)
        writer.write_row(timestamp=time(), bias=bias, current=current)
        current_str = f'Current={current:.3E}A'
    
    # Take n_meas > 1 measurements
    else:
        current = np.zeros(shape=n_meas, dtype=float)
        for i in range(n_meas):
            current[i] = smu_utils.get_current_reading(smu=smu)
            sleep(meas.MEAS_DELAY)

        writer.write_row(timestamp=time(), bias=bias, mean_current=current.mean(), std_current=current.std())
        current_str = 'Current=({:.3E}{}{:.3E})A'.format(current.mean(), u'\u00B1', current.std())

    # Update progressbars poststr
    pbar.set_postfix_str(current_str)

    if log:
        # Construct string
        log = 'INFO @ {} -> Bias={:.3f}V, {}'.format(strftime('%d-%m-%Y %H:%M:%S'), bias, current_str)
        pbar.write(log)


def iv_scan(outfile, smu_setup, bias_voltage, current_limit, bias_polarity=1, bias_steps=None, n_meas=1, smu_name=None, log_progress=False, linger=False, **writer_kwargs):
    """
    Basic IV scan using a single source-measure unit (SMU).

    Parameters
    ----------
    outfile : str
        Output file to write to. By default the type is CSV, can be changed by passing the respective kwargs via **writer_kwargs
    smu_setup : str, dict, File, basil.dut.Dut
        Config file passed to basil.dut.Dut of the respective SMU or already initialized Dut
    bias_voltage : float, int
        Maximum voltage to which the bias voltage is ramped
    current_limit : float
        Current limit in A
    bias_polarity : int, optional
        Bias voltage polarity, - 1 if *bias_polarity* < 0 else 1, by default 1
    bias_steps : int, optional
        If not None, *bias_voltage* is ramped in *bias_steps* equidistant steps using numpy.linspace, by default None
    n_meas : int, optional
        Number of measurements per voltage step. If *n_meas* > 1, the mean is taken
    smu_name : str, optional
        If given, it is used as smu = Dut[*smu_name*] to extract the SMU, if None *smu_setup* can only have one SMU, by default None
    log_progress: bool, optional
        Whether to print the measurements of each voltage step persistently over the progressbar
    linger : bool, float, optional
        Whether to continue measuring IV when the *bias_voltage* has been reached. If True, measure until user interrupt, else measure *linger* seconds
    """

    # We already have an initialized DUT
    if isinstance(smu_setup, Dut):
        dut = smu_setup
    else:
        # Initialize dut
        dut = Dut(smu_setup)
        dut.init()

    # Get SMU from dut
    # By name
    if smu_name:
        smu = dut[smu_name]

    # By being the only hardware
    elif len(dut._hardware_layer) == 1:
        smu, = dut._hardware_layer.values()  # Fancy x, = container syntax

    else:
        msg = "*smu_setup* contains more than 1 hardware driver, cannot identify SMU."
        msg += "Set *smu_name* or only have the SMU hardware driver in *smu_setup*"
        raise ValueError(msg)

    # Generate array of bias voltages to loop over
    bias_volts = smu_utils.generate_bias_volts(bias=bias_voltage, steps=bias_steps, polarity=bias_polarity)

    # Stuff for the DataWriter
    # Prepare comments
    # Check if comments are in writer_kwargs and replace if so
    if 'comments' not in writer_kwargs:
        writer_kwargs['comments'] = [f'SMU: {smu.get_name().strip()}',
                                     f'Current limit: {current_limit:.2E} A',
                                     f'Measurements per voltage step: {n_meas}',
                                     f"Bias voltages: ({', '.join(str(bv) for bv in bias_volts)}) V"]
    
    # Don't allow the user to set the columns
    writer_kwargs['columns'] = ['timestamp', 'bias', 'current'] if n_meas == 1 else ['timestamp', 'bias', 'mean_current', 'std_current']
    
    if 'outtype' in writer_kwargs and writer_kwargs['outtype'] == DataWriter.TABLES:
        writer_kwargs['columns'] = np.dtype(list(zip(writer_kwargs['columns'], [float] * len(writer_kwargs['columns']))))

    # Make instance of data writer
    data_writer = DataWriter(outfile=outfile, **writer_kwargs)

    # Setup our SMU
    smu_utils.setup_voltage_source(smu=smu, bias_voltage=bias_volts, current_limit=current_limit)

    # Ensure we start from 0 volts
    smu_utils.ramp_voltage(smu=smu, target_voltage=0)
    
    try:

        with data_writer as writer:

            # Make progress bar to loop over voltage steps
            pbar_volts = tqdm(bias_volts, unit='bias voltage', desc='IV curve basic')

            # Start looping over voltages
            for bias in pbar_volts:
                
                # Set next voltage
                smu.set_voltage(bias)
    
                # Read current 
                current = smu_utils.get_current_reading(smu=smu)

                # Check if we are above the current limit
                if current  > current_limit and current < 1e37:
                    warnings.warn(f"Current limit exceeded with {current:.2E} A. Abort.", Warning)
                    break
                
                # Let the voltage settle
                sleep(meas.BIAS_SETTLE_DELAY)
            
                _measure_and_write_current(smu=smu, n_meas=n_meas,bias=bias, writer=writer, pbar=pbar_volts, log=log_progress)

            # Loop did not break so there is no current exceeded
            else:

                pbar_volts.close()

                # We want to linger at maximum bias
                if linger:
                    
                    # We linger for fixed amount of seconds
                    if type(linger) in (int, float):
                        start = time()
                        condition = lambda: time() - start <= linger 
                        description = f"Linger for {linger} seconds @ {bias} V..."
                    # We liner indefinetely
                    elif type(linger) is bool:
                        condition = lambda: True
                        description = f"Linger indefinetely @ {bias} V..."
                    else:
                        raise ValueError("*Linger* needs to be bool or number of seconds")

                    # Generator for tqdm yielding while *cond* is true
                    def linger_loop(cond):
                        while cond():
                            yield

                    # Make progresbar
                    pbar_linger = tqdm(linger_loop(cond=condition), unit=' Measurements', desc=description)
                    pbar_linger.write("Press CTRL-C to exit...")

                    # Start lingering
                    try:
                        for _ in pbar_linger:
                            _measure_and_write_current(smu=smu, n_meas=n_meas,bias=bias, writer=writer, pbar=pbar_linger, log=log_progress)
                        pbar_linger.close()
                    except KeyboardInterrupt:
                        # Discard anyting on the transfer layer buffer
                        smu._intf.read()

    finally:

        # Ensure we go back to 0 volts with the same stepping as IV measurements
        smu_utils.ramp_voltage(smu=smu, target_voltage=0, steps=len(bias_volts))

        smu_utils.call_method_if_exists(smu, 'off')

        dut.close()
