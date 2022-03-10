"""
This file contains functions for standalone CV measurements
"""

import warnings
import numpy as np
import silab_collections.meas as meas
from silab_collections.meas.data_writer import DataWriter
from silab_collections.meas.utils import get_current_reading, ramp_voltage
from basil.dut import Dut
from tqdm import tqdm
from time import time, sleep, strftime
from collections import Iterable


def cv_scan(outfile, cv_config, smu_name, lcr_name, bias_voltage, ac_voltage, ac_frequency, current_limit, bias_polarity=1, bias_steps=None, n_meas=1, log_progress=False, **writer_kwargs):
    """
    CV scan using a single source-measure unit (SMU) as well as the HPLCR meter.

    Parameters
    ----------
    outfile : str
        Output file to write to. By default the type is CSV, can be changed by passing the respective kwargs via **writer_kwargs
    smu_config : str, dict, File
        Config file passed to basil.dut.Dut of the respective SMU
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
        If given, it is used as smu = Dut[*smu_name*] to extract the SMU, if None *smu_config* can only have one SMU, by default None
    log_progress: bool, optional
        Whether to print the measurements of each voltage step persistently over the progressbar 
    """

    # Initial check for HP 4284A LCR meter which is needed
    if not any(hwd['type'] == 'hp4284a' for hwd in cv_config['hw_drivers']):
        raise RuntimeError("This measurement script requires the HP 4284A LCR meter")


    # Initialize dut
    dut = Dut(cv_config)
    dut.init()

    # Get SMU from dut
    smu = dut[smu_name]

    # get LCR meter by name
    lcr = dut[lcr_name]

    # Stuff for the DataWriter
    # Prepare comments
    # Check if comments are in writer_kwargs and replace if so
    if 'comments' not in writer_kwargs:
        writer_kwargs['comments'] = [f'SMU: {smu.get_name()}',
                                     f'LCR meter: {lcr.get_name()}',
                                     f'AC voltage: {ac_voltage} V @ {ac_frequency} Hz',
                                     f'Current limit: {current_limit:.2E} A',
                                     f'Measurements per voltage step: {n_meas}']
    
    # Prepare output file type
    if 'outtype' not in writer_kwargs:
        writer_kwargs['outtype'] = DataWriter.CSV  
    
    # Don't allow the user to set the columns
    if n_meas == 1:
        writer_kwargs['columns'] = ['timestamp', 'bias', 'current', 'cp', 'rp']
    else:
        writer_kwargs['columns'] = ['timestamp', 'bias', 'mean_current', 'std_current', 'mean_cp', 'std_cp', 'mean_rp', 'std_rp']
    
    if writer_kwargs['outtype'] == DataWriter.TABLES:
        writer_kwargs['columns'] = np.dtype(list(zip(writer_kwargs['columns'], [float] * len(writer_kwargs['columns']))))

    # Make instance of data writer
    data_writer = DataWriter(outfile=outfile, **writer_kwargs)

    # Create voltage steps etc.
    if isinstance(bias_voltage, Iterable):
        try:
            bias_volts = [float(bv) for bv in bias_voltage]
            writer_kwargs['comments'].append('Bias voltages: ({}) V'.format(', '.join(str(bv) for bv in bias_volts)))
        except ValueError:
            raise ValueError("*bias_voltage* must be iterable of voltages convertable to floats")
    else:
        bias_polarity = 1 if bias_polarity > 0 else -1
        max_bias = bias_polarity * bias_voltage
        if bias_steps is None:
            bias_volts = np.linspace(0, max_bias, int(abs(max_bias)+1))
        else:
            bias_volts = np.linspace(0, max_bias, int(bias_steps))

        writer_kwargs['comments'].append(f'Bias voltage: {max_bias} V in {(abs(max_bias) + 1) / len(bias_volts)} V steps')

    # Adjust the SMU from basil if possible
    # Ensure we are in voltage sourcing mode
    if hasattr(smu, 'source_voltage'):
        smu.source_volt()
    
    # Ensure compliance limit
    if hasattr(smu, 'set_current_limit'):
        smu.set_current_limit(current_limit)

    # Ensure voltage range
    if hasattr(smu, 'set_voltage_range'):
        smu.set_voltage_range(float(np.max(np.abs(bias_voltage))) if isinstance(bias_voltage, list) else bias_voltage)

    # Switch on SMU if possible from basil
    if hasattr(smu, 'on'):
        smu.on()

    # Ensure we start from 0 volts
    ramp_voltage(device=smu, target_voltage=0, steps=bias_steps)
    
    try:

        with data_writer as writer:

            # Make progress bar to loop over voltage steps
            pbar_volts = tqdm(bias_volts, unit='bias steps', desc='CV scan')

            # Start looping over voltages
            for bias in pbar_volts:
                
                # Set next voltage
                smu.set_voltage(bias)
    
                # Read current 
                current = get_current_reading(device=smu)

                # Check if we are above the current limit
                if current  > current_limit and current < 1e37:
                    warnings.warn(f"Current limit exceeded with {current:.2E} A. Abort.", Warning)
                    break
                
                # Let the voltage settle
                sleep(meas.BIAS_SETTLE_DELAY)
            
                # We only take one measurement
                if n_meas == 1:
                    current = get_current_reading(device=smu)
                    cp, rp = lcr.CPRP
                    writer.write_row(timestamp=time(), bias=bias, current=current, cp=cp, rp=rp)
                    current_str = f'Current={current:.3E}A'
                
                # Take n_meas > 1 measurements
                else:
                    current = cp = rp = (np.zeros(shape=n_meas, dtype=float) for _ in range(3))
                    for i in range(n_meas):
                        current[i] = get_current_reading(device=smu)
                        cp[i], rp[i] = lcr.CPRP
                        sleep(meas.MEAS_DELAY)

                    writer.write_row(timestamp=time(), bias=bias, mean_current=current.mean(), std_current=current.std(), mean_cp=cp.mean(), std_cp=cp.std(), mean_rp=rp.mean(), std_rp=rp.std())
                    current_str = 'Current=({:.3E}{}{:.3E})A'.format(current.mean(), u'\u00B1', current.std())
                
                # Update progressbars poststr
                pbar_volts.set_postfix_str(current_str)

                if log_progress:
                    # Construct string
                    log = 'INFO @ {} -> Bias={:.3f}V, {}'.format(strftime('%d-%m-%Y %H:%M:%S'), bias, current_str)
                    pbar_volts.write(log)

    finally:

        lcr.ac_voltage = 'MIN'

        # Ensure we go back to 0 volts with the same stepping as IV measurements
        ramp_voltage(device=smu, target_voltage=0, steps=bias_steps)

        if hasattr(smu, 'off'):
            smu.off()
