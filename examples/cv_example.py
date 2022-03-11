from silab_collections.meas import cv


def cv_scan_example():
    """
    Make sure that the *smu_config* describes your setup
    """

    # Basil configuration: adapt to your actual hardware
    cv_config = {
        'transfer_layer': 
            [
            {'name': 'Visa',
             'type': 'Visa',
             'init': {'resource_name': 'GPIB0::17::INSTR'}},
            {'name': 'Serial',
             'type': 'Serial',
             'init': {'port': 'COM7',  # Currently LCR meter oly works on windows
                      'read_termination': '\r\n',
                      'baudrate': 19200}} 
            ],
        'hw_drivers':
            [
            {'name': 'LCRMeter',
             'type': 'hp4284a',
             'interface': 'Visa',
             'init': {'device': 'HP 4284A'}},
            {'name': 'Sourcemeter',
             'type': 'scpi',
             'interface': 'Serial',
             'init': {'device': 'Keithley 2410'}}
            ]
    }

    # CV scan
    cv.cv_scan(outfile='cv_scan_example.csv',
               cv_config=cv_config,
               smu_name='Sourcemeter',
               lcr_name='LCRMeter',
               ac_voltage=5e-3,
               ac_frequency=1e3,
               bias_polarity=30,
               current_limit=20e-6,
               overwrite=True)  # DataWriter


if __name__ == '__main__':
    cv_scan_example()
