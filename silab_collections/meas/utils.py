import numpy as np
from tqdm import tqdm
from time import sleep


def get_device_type(device):
        basil_identifier = device.get_name().split(',')
        if len(basil_identifier) > 1:
            vendor = basil_identifier[0].split(' ')[0].upper()
            model = basil_identifier[1].split(' ')[-1].upper()
            return f'{vendor}_{model}'
        else:
            return None


def get_current_reading(device):
    typ = get_device_type(device)
    if typ == 'KEITHLEY_2410':
        return float(device.get_current().split(',')[1])
    elif typ == 'KEITHLEY_6517A'.upper():
        return float(device.get_current().split(',')[0][:-4])
    else:
        return float(device.get_current().split(',')[0])  # [1]


def get_voltage_reading(device):
    typ = get_device_type(device)
    if typ == 'KEITHLEY_2410':
        return float(device.get_voltage().split(',')[0])
    elif typ == 'KEITHLEY_6517A':
        return float(device.get_voltage().split(',')[0][:-4])
    else:
        return float(device.get_voltage().split(',')[0])


def ramp_voltage(device, target_voltage=0, delay=1, steps=None):
    """
    Ramps the voltage from the current value to *aim_voltage* with stopping *ramp_delay* seconds in between.

    Parameters
    ----------
    device : basil.dut.Dut
        Initialized basil device which as get/set_voltage method
    target_voltage : int, optional
        The voltage to ramp to, by default 0
    delay : int, optional
        Delay in between voltage steps in seconds, by default 1
    steps: int, optional
        The amount of steps used for, by default None
    """

    # Check for voltage getter and setter
    if not all(hasattr(device, f'{x}_voltage') for x in ('get', 'set')):
        raise AttributeError('device does not have voltage getter/setter methods')

    # Get the current voltage
    current_voltage = get_voltage_reading(device=device)

    # If we are already at the aim voltage, return
    if  current_voltage == target_voltage:
        return

    # Create voltages to loop through
    if steps is None:
        volts = np.linspace(current_voltage, target_voltage, abs(target_voltage-current_voltage)+1) 
    else:
        volts = np.linspace(current_voltage, target_voltage, steps)
    # Make progressbar
    pbar_ramp = tqdm(volts, unit='voltage steps', desc=f'Ramping voltage to {target_voltage} V')
    
    for v in pbar_ramp:
        # Set voltage
        device.set_voltage(v)

        # Update pbar text
        pbar_ramp.set_postfix_str(f'Voltage={v:.2f}V')
        
        # Wait
        sleep(delay)

    # Get the current voltage
    current_voltage = get_voltage_reading(device=device)

    if current_voltage != target_voltage:
        raise RuntimeError(f"Ramping voltage to target of {target_voltage} V failed. ({current_voltage} V after ramping.")
