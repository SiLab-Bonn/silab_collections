"""
The examples in this file use the DataWriter class to write data to different file types 
"""

import numpy as np
import tables as tb
from silab_collections.meas.data_writer import DataWriter
from time import asctime, time


# Create some variables
OUTFILE = './example_data'
COLMUNS = np.dtype([('timestamp', '<f8'), ('voltage', '<f4'), ('current', '<f4')])
IDENTIFIER = "IV_curve"
COMMENTS = (f"Measured on {asctime()}",
            "SMU: Keithley 2410",
            "Temperature: 20 C")

def write_csv_example():

    print("### DataWriter Example with CSV output file ###\n")

    # Initialize and enter context
    with DataWriter(outfile=OUTFILE,
                    columns=COLMUNS.names,
                    identifier=IDENTIFIER,
                    comments=COMMENTS,
                    overwrite=True) as writer:
        
        # Write some data
        writer.write_row(time(), 10.0, 1e-6)
        writer.write_row(timestamp=time(), voltage=20.0, current=2e-6)

    print(f"File content of {OUTFILE}.csv", '\n')
    with open(f'{OUTFILE}.csv', 'r') as f:
        for l in f.readlines():
            print(l)


def write_h5_example():

    print("### DataWriter Example with HDF5 output file ###\n")
    
    with DataWriter(outfile=OUTFILE,
                    columns=COLMUNS,
                    outtype=DataWriter.TABLES,
                    identifier=IDENTIFIER,
                    comments=COMMENTS,
                    overwrite=True) as writer:
        
        writer.write_row(time(), 10.0, 1e-6)
        writer.write_row(timestamp=time(), voltage=20.0, current=2e-6)

    print(f"File content of {OUTFILE}.h5", '\n')
    with tb.open_file(f'{OUTFILE}.h5', 'r') as f:
        print(f)
        for l in f.walk_nodes():
            if hasattr(l, 'colnames'):
                print('({})'.format(', '.join(l.colnames)))
                for ll in l.cols:
                    print(ll)


if __name__ == '__main__':
    write_csv_example()
    print('\n' * 3)
    write_h5_example()