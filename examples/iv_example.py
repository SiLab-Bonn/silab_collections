import silab_collections.meas as meas
from silab_collections.meas import iv
from silab_collections.meas.data_writer import DataWriter


def iv_scan_example():
    """
    In this example 3 basic IV scans are described with different parameters.
    Uncomment to run different scans.
    Make sure that the *smu_config* describes your setup
    """

    # Basil configuration: adapt to your actual hardware
    smu_config = {
        'transfer_layer': 
            [{'name': 'Serial',
              'type': 'Serial',
              'init': {'port': '/dev/ttyUSB0',
                       'read_termination': '\r',
                       'baudrate': 19200}}],
        'hw_drivers':
            [{'name': 'Sourcemeter',
              'type': 'scpi',
              'interface': 'Serial',
              'init': {'device': 'Keithley 2410'}}]
    }

    # Do iv scan
    iv.iv_scan(outfile='iv_scan_basic_example_1.csv',
               smu_config=smu_config,
               bias_voltage=60,  # IV scan from 0 to 60 V in 1 V steps
               current_limit=1e-6,  # Current limit in A
               n_meas=10,  # Take 10 measurements per given bias voltage and take the mean
               overwrite=True)  # Additional kwargs are passed to the writer

    # # Adjust measurement delays to your needs
    # meas.MEAS_DELAY = 0.2  # Delay in between consecutive measurments in seconds, defaults to 0.1
    # meas.BIAS_SETTLE_DELAY = 5  # Delay for new bias voltage to settle in seconds, defaults to 1

    # # Do iv scan
    # iv.iv_scan(outfile='iv_scan_basic_example_2.h5',
    #                  smu_config=smu_config,
    #                  bias_voltage=60,  # IV scan from 0 to 60 V in *bias_steps* equidistant steps
    #                  current_limit=1e-6,  # Current limit in A
    #                  bias_steps=20,  # Take 20 equidistant measurements between 0 and 60 V, same as bias_voltage=np.linspace(0, 60, 20)
    #                  overwrite=True,  # Additional kwargs are passed to the writer
    #                  outtype=DataWriter.TABLES)  # Additional kwargs are passed to the writer

    # # Do iv scan
    # iv.iv_scan(outfile='iv_scan_basic_example_3.h5',
    #                  smu_config=smu_config,
    #                  bias_voltage=[0, 1, 2, 3, 4, 5, 10, 15, 20],  # IV scan with custom voltages
    #                  current_limit=1e-6,  # Current limit in A
    #                  log_progress=True,  # Show measurements of each bias step above progressbar
    #                  overwrite=True,  # Additional kwargs are passed to the writer
    #                  outtype=DataWriter.TABLES)  # Additional kwargs are passed to the writer


if __name__ == '__main__':
    iv_scan_example()