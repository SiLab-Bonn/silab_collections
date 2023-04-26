"""
Script containing SMU-related functionality
"""

import numpy as np
from tqdm import tqdm
from time import sleep
from collections.abc import Iterable


def call_method_if_exists(smu, method, *args, **kwargs):

    try:
        # The getattr will always succeed and return a callable which will fail with ValueError if they are not defined on the smu.
        return getattr(smu, method)(*args, **kwargs)
    except ValueError:
        pass


def get_smu_type(smu):
        basil_identifier = smu.get_name().split(',')
        if len(basil_identifier) > 1:
            vendor = basil_identifier[0].split(' ')[0].upper()
            model = basil_identifier[1].split(' ')[-1].upper()
            return f'{vendor}_{model}'
        else:
            return None


def get_current_reading(smu):

    # Life is easier with formatting
    if hasattr(smu, 'has_formatting') and smu.has_formatting:
        if not smu.formatting_enabled:
            smu.enable_formatting()
        return float(smu.get_current())
    else:
        # Specifiy different smu type responses here; if not specified expect smu has get_current return value
        typ = get_smu_type(smu)
        if typ == 'KEITHLEY_2410':
            return float(smu.get_current().split(',')[1])
        elif typ == 'KEITHLEY_6517A':
            return float(smu.get_read().split(',')[0][:-4])
        else:
            return float(smu.get_current())


def get_voltage_reading(smu):

    # Life is easier with formatting
    if hasattr(smu, 'has_formatting') and smu.has_formatting:
        if not smu.formatting_enabled:
            smu.enable_formatting()
        return float(smu.get_voltage())
    else:
        typ = get_smu_type(smu)
        if typ == 'KEITHLEY_2410':
            return float(smu.get_voltage().split(',')[0])
        elif typ == 'KEITHLEY_6517A':
            return float(smu.get_voltage())
        else:
            return float(smu.get_voltage())

def generate_bias_volts(bias, steps=None, polarity=1, check_monotonic=True):
    """
    Create and return a np.array of bias voltages.
    If step is None and bias is a number, np.linspace is used and creates *bias* voltages.
    If *bias* is already an iterable of voltages, checks are performed.

    Parameters
    ----------
    bias : float, int, Iterable of float/int
        Bias voltage(s)
    steps : int, None
        Number of steps to generate for bias, by default None.
    polarity : int
        Polarity of the bias viltage; either -1 or +1
    check_monotonic : bool
        Whether to check if the *bias* input is monotonic; only applies if *bias* is an Iterable

    Raises
    ------
    ValueError
        Not all contents of *bias* can be converted to floats or are not monotonic

    Returns
    -------
    np.array
        Array of bias voltages
    """

    is_monotonic = lambda a: all(a[i] <= a[i+1] for i in range(len(a)-1)) or all(a[i] >= a[i+1] for i in range(len(a)-1))

    # Create voltage steps etc.
    if isinstance(bias, Iterable):
        try:
            bias_volts = np.array([float(bv) * polarity for bv in bias])
        except ValueError:
            raise ValueError("*bias* must be iterable of voltages convertable to floats")

        if check_monotonic and not is_monotonic(bias_volts):
            raise ValueError("*bias* iterable is not monotonic. Set check_monotonic=False to skip this check")
    else:
        bias_polarity = 1 if polarity >= 0 else -1
        max_bias = bias_polarity * bias
        if steps is None:
            bias_volts = np.linspace(0, max_bias, int(abs(max_bias)+1))
        else:
            bias_volts = np.linspace(0, max_bias, int(steps))

    return bias_volts

def setup_voltage_source(smu, bias_voltage, current_limit):
    """
    Sets up the *smu* to provide a voltage source.
    Set SMU-specific parameters such as the operating voltage range
    as well as the current compliance limit.

    Parameters
    ----------
    smu : basil.dut.Dut.HardwareLayer
        Harwdare layer of the SMU
    bias_voltage : int, float, iterable of int, float
        Voltage(s) of which the maximum is determined to set the range
    current_limit : float, int
        Current compliance limit in A
    """

    # Adjust the SMU from basil if possible
    # Ensure we are in voltage sourcing mode
    call_method_if_exists(smu, 'source_volt')
    
    # Ensure compliance limit
    call_method_if_exists(smu, 'set_current_limit', current_limit)

    # Ensure voltage range
    call_method_if_exists(smu, 'set_voltage_range', float(np.max(np.abs(bias_voltage)) if isinstance(bias_voltage, Iterable) else np.abs(bias_voltage)))

    # Check if smu is already on
    smu_is_on = call_method_if_exists(smu, 'get_on')
    if smu_is_on is not None and bool(smu_is_on.strip()):
        # If smu is already on we want to ramp down to 0 volt
        ramp_voltage(smu, delay=0.2)
    # if we cannot tell, just ramp to 0 and turn on
    else:
        call_method_if_exists(smu, 'set_voltage', 0)
        call_method_if_exists(smu, 'on')


def ramp_voltage(smu, target_voltage=0, delay=1, steps=None):
    """
    Ramps the voltage from the current value to *aim_voltage* with stopping *ramp_delay* seconds in between.

    Parameters
    ----------
    smu : basil.dut.Dut.HardwareLayer
        Initialized basil smu which as get/set_voltage method
    target_voltage : int, optional
        The voltage to ramp to, by default 0
    delay : int, optional
        Delay in between voltage steps in seconds, by default 1
    steps: int, optional
        The amount of steps used for, by default None

    Raises
    ------
    AttributeError:
        SMU does not have voltage getter/setter
    """

    smu_is_on = call_method_if_exists(smu, 'get_on')
    if smu_is_on is not None:
        if not int(smu_is_on.strip()):
            call_method_if_exists(smu, 'on')

    # Get the current voltage
    current_voltage = get_voltage_reading(smu=smu)

    # If we are already at the aim voltage, return
    if  current_voltage == target_voltage:
        return

    # Create voltages to loop through
    if steps is None:
        volts = np.linspace(current_voltage, target_voltage, int(abs(target_voltage-current_voltage)+2)) 
    else:
        volts = np.linspace(current_voltage, target_voltage, int(steps))
    
    # Make progressbar
    pbar_ramp = tqdm(volts, unit='voltage steps', desc=f'Ramping voltage to {target_voltage} V')
    
    for v in pbar_ramp:
        # Set voltage
        smu.set_voltage(v)

        # Update pbar text
        pbar_ramp.set_postfix_str(f'Voltage={v:.2f}V')
        
        # Wait
        sleep(delay)

    # Get the current voltage
    current_voltage = get_voltage_reading(smu=smu)

    if not np.isclose(current_voltage, target_voltage, atol=1):
        raise RuntimeError(f"Ramping voltage to target of {target_voltage} V failed. ({current_voltage} V after ramping.")
