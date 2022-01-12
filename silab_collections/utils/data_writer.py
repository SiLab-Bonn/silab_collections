"""
Implemenntation of a context manager *DataWriter* enabling writing data row by row into a file.
*DataWriter* enables writing to a comma separated value (CSV) file or as well as HDF5 binary file.
"""

import os
import csv
import numpy as np
import tables as tb


class DataWriter:
    """
    Context manager for writing data to CSV or HDF5 binary file.
    Typical use-case are simple measurements such as IV or CV curves.
    """

    # Define static class attributes used for identifying output file type
    CSV: int = 0
    TABLES: int = 1
    _FILE_EXTENSION: dict = {CSV: '.csv', TABLES: '.h5'}

    def __init__(self, outfile, columns, identifier='measurement', outtype=CSV, comments=None, overwrite=False):
        """
        Parameters
        ----------
        outfile : str
            Path to output file
        columns : list, tuple, np.dtype
            Description of columns the data is written to. In case of outtype=TABLES, must be np.dtype
        identifier : str, optional
            String that identifies in what context the data is taken e.g. 'IV curve', by default 'measurement'
        outtype : int, optional
            Type of output file to be written to, by default DataWriter.CSV (=0)
        comments : str, iterable of str, optional
            Comments which are stored within the outfile, by default None. Useful for storing e.g. conditions
            of the data recording such as temperature, humidity, date, measurement device, etc. 
        overwrite : bool, optional
            Whether to overwrite outfile if it already exists, by default False
        """

        # Store instances init attributes
        self.out_file = outfile
        self.out_type = outtype
        self.comments = comments
        self.columns = columns
        self.identifier = identifier
        self.overwrite = overwrite
        
        # Attribute for storing file handle
        self.file = None

        # Privates 
        self._writer = {}
        self._col_names = None

        # Private methods for setting up the instance
        self._check_extension()
        self._check_sanity()
        self._check_columns()
        self._prepare_comments()

    def _check_sanity(self):
        """
        Do sanity checks

        Raises
        ------
        IOError
            If *self.outfile* already exists and this instance is not allowed to overwrite
        ValueError
            When *self.identifier* is not a non-empty string
        """

        if os.path.isfile(self.out_file) and not self.overwrite:
            msg = f"File {self.out_file} already exists."
            msg += f"Initialize {type(self).__name__} with 'overwrite=True' if you wish to allow overwriting files."
            raise IOError(msg)

        if not self.identifier or not isinstance(self.identifier, str):
            raise ValueError(f"*identifier* must be non-empty string, is '{self.identifier}'")

    def _check_columns(self):
        """
        Check the data columns of the output file

        Raises
        ------
        TypeError
            The *self.out_type* does not have the correct *self.columns* type
        NotImplementedError
            The *self.out_type* is not implemented
        """
        if self.out_type == self.TABLES:
            if not isinstance(self.columns, np.dtype):
                raise TypeError("*columns* must be of type numpy.dtype for *out_type=TABLES*")
            self._col_names = self.columns.names
        elif self.out_type == self.CSV:
            if not isinstance(self.columns, (list, tuple)):
                raise TypeError("*columns* must be list or tuple of names for *out_type=CSV*")
            self._col_names = self.columns
        else:
            raise NotImplementedError(f"Output file type {self.out_type} not supported.")

    def _check_extension(self):
        """
        Check the file extension for the respective *self.out_type* and add it, if not given
        """

        if not self.out_file.lower().endswith(self._FILE_EXTENSION[self.out_type]):
            self.out_file += self._FILE_EXTENSION[self.out_type]

    def _prepare_comments(self):
        """
        Prepare *self.comments* to be written to *self.out_file*

        Raises
        ------
        ValueError
            The comments are not strings or iterables of strings 
        """
        
        if self.comments:
            # If the *self.comments* is a single string we dont have to do anything
            if isinstance(self.comments, str):
                self.comments = [self.comments]
            elif isinstance(self.comments, (list, tuple)):

                if not all(isinstance(c,  str) for c in self.comments):
                    raise ValueError("*comments* must be string or iterable of strings.")
            else:
                raise ValueError("*comments* must be string or iterable of strings.")

    def _open(self):
        """
        Opens the respective *self.out_file* of type *self.out_type*.
        Called from within the __enter__ method

        Raises
        ------
        NotImplementedError
            The *self.out_type* is not implemented
        """

        if self.out_type == self.TABLES:
            self.file = tb.open_file(self.out_file, mode='w')
            self._writer[self.out_type] = self.file.create_table(where=self.file.root,
                                                                 name=self.identifier,
                                                                 description=self.columns,
                                                                 title='Comments: ' + '; '.join(self.comments))
        elif self.out_type == self.CSV:
            self.file = open(self.out_file, mode='w')
            self._writer[self.out_type] = csv.writer(self.file, quoting=csv.QUOTE_NONNUMERIC, quotechar='#')
            
            self.file.write('# Identifier:\n#\t{}\n'.format(self.identifier))
            self.file.write('# Comments:\n#\t{}\n'.format('\n#\t'.join(self.comments)))
            self.file.write('# Columns:\n#\t{}\n'.format(', '.join(self._col_names)))
            
        else:
            raise NotImplementedError(f"Output file type {self.out_type} not supported.")

    def _close(self):
        """
        Close output file. Called from within __exit__ method
        """
        if self.file:
            self.file.close()

    def __enter__(self):
        """
        Context manager entry point

        Returns
        -------
        DataWriter instance
        """
        self._open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_traceback):
        """
        Context manager exit point
        Args are needed for exception handling and arr automatically passed by with statement on exit
        """
        self._close()

    def _write_row(self, data_dict):
        """
        Private method to write a row of data to the *self._out_file* with respect to *self.out_type*

        Parameters
        ----------
        data_dict : dict
            Dictionary with columns names as keys and respective values

        Raises
        ------
        NotImplementedError
            The *self.out_type* is not implemented
        """

        if self.out_type == self.TABLES:
                for col, val in data_dict.items():
                    self._writer[self.out_type].row[col] = val
                self._writer[self.out_type].row.append()
                self._writer[self.out_type].flush()
            
        elif self.out_type == self.CSV:
            self._writer[self.out_type].writerow([data_dict[col] for col in self._col_names])
        else:
            raise NotImplementedError(f"Output file type {self.out_type} not supported.")

    def write_row(self, *row_data, **row_items):
        """
        Method to write row data to *self.out_file* with respect to *self._out_type*.
        If *row_data* is given, it is expected to be in the correct order.
        If *row_items* is given, the keywords must be column names
        Only one of the two must be used

        The following method calls produce the same result (with columns=["col1", "col2", "col3"]):
        
        # Use row_data
        DataWriter.write_row(5, 7, 9)
        
        # Use row_items
        DataWriter.write_row(col2=7, col1=5, col3=9)

        Raises
        ------
        ValueError
            - *row_data* as well as *row_items* is given
            - Given input has not the same length as *self.columns*
        KeyError
            *row_items* is missing a column
        """

        if row_data and row_items:
            raise ValueError(f"Data can either be written as args or keyword args, not both")

        elif row_data:

            if len(row_data) != len(self.columns):
                raise ValueError("*write_row* method requires data for each column of the row!")

            self._write_row(data_dict=dict(zip(self._col_names, row_data)))
        
        else:

            if len(row_items) != len(self.columns):
                raise ValueError("*write_row* method requires data for each column of the row!")

            if not all(k in row_items for k in self._col_names):
                raise KeyError("Column field is missing!")

            self._write_row(data_dict=row_items)
