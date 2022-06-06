"""
This file contains functions for standalone CV measurements
"""

import warnings
import numpy as np
import silab_collections.meas as meas
import silab_collections.meas.smu as smu_utils
from silab_collections.meas.data_writer import DataWriter
from basil.dut import Dut
from tqdm import tqdm
from time import time, sleep, strftime


def cv_scan(outfile, cv_config, smu_name, lcr_name, ac_voltage, ac_frequency, bias_voltage, current_limit, lcr_func='CPRP', bias_polarity=1, bias_settle_delay=5, bias_steps=None, n_meas=1, log_progress=False, **writer_kwargs):
    """
    CV scan using a single source-measure unit (SMU) as well as the HP4284A LCR meter.

    Parameters
    ----------
    outfile : str
        Output file to write to. By default the type is CSV, can be changed by passing the respective kwargs via **writer_kwargs
    cv_config : str, dict, File
        Config file passed to basil.dut.Dut of the respective setup devices, namely one SMU and LCR meter
    smu_name : str
        Name of SMU given in *cv_config*
    lcr_name : str
        Name of LCR meter given in *cv_config*
    ac_voltage: float
        The AC voltage of the LCR meter in V. Typical values are in the order of 5 mV
    ac_frequency: float
        The AC frequency of *ac_voltage*, Typical values ar in the order of 1kHz (10kHz for irradiated devices)
    bias_voltage : float, int, Iterable
        Voltage to which is ramped in V. Can also be an Iterable of voltages to use instead
    current_limit : float
        Current limit in A
    lcr_func : str, optinal
        Measurement function of the LCR meter as defined in h2484a.MEAS_FUNCS, by default 'CPRP'
    bias_polarity : int, optional
        Bias voltage polarity (bias will be calculated by polarity * bias_voltage), - 1 if *bias_polarity* < 0 else 1, by default 1
    bias_settle_delay : float
        Number of seconds to wait after a new bias voltage has been set before taking a measurement, by default 5. Needs to increase with capacitance
    bias_steps : int, optional
        If not None, *bias_voltage* is ramped in *bias_steps* equidistant steps using numpy.linspace, by default None
    n_meas : int, optional
        Number of measurements per voltage step. If *n_meas* > 1, the mean is taken
    log_progress: bool, optional
        Whether to print the measurements of each voltage step persistently over the progressbar 
    """
    # Set bias settle delay to 5 seconds for large capacitances
    meas.BIAS_SETTLE_DELAY = bias_settle_delay
    
    # Initialize dut
    dut = Dut(cv_config)
    dut.init()

    # Initial check for HP 4284A LCR meter which is needed
    if not any(hwd['type'] == 'hp4284a' for hwd in dut._conf['hw_drivers']):
        raise RuntimeError("This measurement script requires the HP 4284A LCR meter")

    # Get SMU and LCR meter from dut
    smu, lcr = dut[smu_name], dut[lcr_name]

    # Generate array of bias voltages to loop over
    bias_volts = smu_utils.generate_bias_volts(bias=bias_voltage, steps=bias_steps, polarity=bias_polarity)

    # Stuff for the DataWriter
    # Prepare comments
    # Check if comments are in writer_kwargs and replace if so
    if 'comments' not in writer_kwargs:
        writer_kwargs['comments'] = [f'SMU: {smu.get_name().strip()}',
                                     f'LCR meter: {lcr.get_name().strip()}',
                                     f'LCR measurement function: {lcr.get_meas_func().strip()}',
                                     f'AC voltage: {ac_voltage} V @ {ac_frequency} Hz',
                                     f'Current limit: {current_limit:.2E} A',
                                     f'Measurements per voltage step: {n_meas}',
                                     f"Bias voltages: ({', '.join(str(bv) for bv in bias_volts)}) V"]
    
    # Don't allow the user to set the columns
    if n_meas == 1:
        writer_kwargs['columns'] = ['timestamp', 'bias', 'current', 'primary', 'secondary']
    else:
        writer_kwargs['columns'] = ['timestamp', 'bias', 'mean_current', 'std_current', 'mean_primary', 'std_primary', 'mean_secondary', 'std_secondary']
    
    if 'outtype' in writer_kwargs and writer_kwargs['outtype'] == DataWriter.TABLES:
        writer_kwargs['columns'] = np.dtype(list(zip(writer_kwargs['columns'], [float] * len(writer_kwargs['columns']))))

    # Make instance of data writer
    data_writer = DataWriter(outfile=outfile, **writer_kwargs)

    # Setup our SMU
    smu_utils.setup_voltage_source(smu=smu, bias_voltage=bias_volts, current_limit=current_limit)

    # Ensure we start from 0 volts
    smu_utils.ramp_voltage(smu=smu, target_voltage=0)
    
    # Set AC parameters
    lcr.ac_voltage = ac_voltage
    lcr.frequency = ac_frequency
    lcr.set_meas_func(lcr_func)
    lcr.set_trigger_mode('HOLD')
    
    try:

        with data_writer as writer:

            # Make progress bar to loop over voltage steps
            pbar_volts = tqdm(bias_volts, unit='bias voltage', desc='CV scan')

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
            
                # We only take one measurement
                if n_meas == 1:
                    current = smu_utils.get_current_reading(smu=smu)
                    primary, secondary = getattr(lcr, lcr_func)
                    writer.write_row(timestamp=time(), bias=bias, current=current, primary=primary, secondary=secondary)
                    meas_str = f'LCR function: {lcr_func}, Primary: {primary:.3E}, Secondary: {secondary:.3E}'
                    current_str = f'Current={current:.3E}A'
                
                # Take n_meas > 1 measurements
                else:
                    current, primary, secondary = (np.zeros(shape=n_meas, dtype=float) for _ in range(3))
                    for i in range(n_meas):
                        current[i] = smu_utils.get_current_reading(smu=smu)
                        primary[i], secondary[i] = getattr(lcr, lcr_func)
                        sleep(meas.MEAS_DELAY)

                    writer.write_row(timestamp=time(), bias=bias, mean_current=current.mean(), std_current=current.std(),
                                     mean_primary=primary.mean(), std_primary=primary.std(), mean_secondary=secondary.mean(),
                                     std_secondary=secondary.std())
                    meas_str = "LCR function: {}, Primary: ({:.3E}{}{:.3E}), Secondary: ({:.3E}{}{:.3E})".format(lcr_func,
                                                                                                                 primary.mean(),
                                                                                                                 u'\u00B1',
                                                                                                                 primary.std(),
                                                                                                                 secondary.mean(),
                                                                                                                 u'\u00B1', 
                                                                                                                 secondary.std())
                    current_str = 'Current=({:.3E}{}{:.3E})A'.format(current.mean(), u'\u00B1', current.std())
                
                # Update progressbars poststr
                pbar_volts.set_postfix_str(current_str)

                if log_progress:
                    # Construct string
                    log = 'INFO @ {} -> Bias={:.3f}V, {} -> {}'.format(strftime('%d-%m-%Y %H:%M:%S'), bias, current_str, meas_str)
                    pbar_volts.write(log)

    finally:

        lcr.ac_voltage = 'MIN'

        # For CV the voltage can sometimes be not 0 after the ramping due to large capacitances which are measured keeping the voltage higher
        try:
            # Ensure we go back to 0 volts with the same stepping as IV measurements
            smu_utils.ramp_voltage(smu=smu, target_voltage=0, steps=len(bias_volts))
        except RuntimeError:
            pass
        
        if hasattr(smu, 'off'):
            smu.off()

        dut.close()
