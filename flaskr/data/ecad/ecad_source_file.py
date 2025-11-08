#!/usr/bin/python3
"""Class representing an ecad file with source data."""
# Created: jue sep 12 08:56:31 2024 (+0200)
# Last-Updated: mar sep 24 17:11:22 2024 (+0200)
# Filename: ecad_source_files.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
import math
from datetime import datetime, timezone

from data.averages import Average

from db.statements import Statements

from flask import current_app

import pandas as pd


class EcadSourceFile():
    """Class representing an ecad file with source data."""

    def __init__(self, provider_id, filepath, magnitude_id, meas_data):
        """Initialize class."""
        self._provider_id = provider_id
        self._filepath = filepath
        self._magnitude_id = magnitude_id
        self._measurement_id = meas_data[0]
        self._measurement_name = meas_data[1]
        self._measurement_alias = meas_data[2]
        self._station_id = None
        self._source_id = None
        self._start_valid_data_date = None
        self._end_valid_data_date = None
        self._factor = None
        self._unit = None
        self._measurement_type = None
        self._participant_name = None

        self._processed = False

        self.stmt = Statements()

    def __getstate__(self):
        """Delete objects not suitable for pickle."""
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes. Always use the dict.copy()
        # method to avoid modifying the original state.
        state = self.__dict__.copy()
        # Remove the unpicklable entries.
        del state['stmt']

        return state

    def __setstate__(self, state):
        """Restore objects which was not pickled."""
        # Restore instance attributes (i.e., filename and lineno).
        self.__dict__.update(state)
        # Restore the statements object
        self.stmt = Statements()

    @property
    def filepath(self):
        """Return the file path."""
        return self._filepath

    @property
    def station_id(self):
        """Return the station identifier."""
        return self._station_id

    @property
    def magnitude_id(self):
        """Return the magnitude identifier."""
        return self._magnitude_id

    @property
    def magnitude_name(self):
        """Return the magnitude name."""
        return self.stmt.get_magnitude_name(self._provider_id, self._magnitude_id)

    @property
    def source_id(self):
        """Return the source identifier."""
        return self._source_id

    @property
    def start(self):
        """Return the date where first valid data is detected."""
        return self._start_valid_data_date

    @start.setter
    def start(self, date_start):
        """Set the start valid date."""
        self._start_valid_data_date = date_start

    @property
    def end(self):
        """Return the date where last valid data is detected."""
        return self._end_valid_data_date

    @end.setter
    def end(self, date_end):
        """Set the end valid date."""
        self._end_valid_data_date = date_end

    @property
    def meas_alias(self):
        """Return the Ecad measurement alias."""
        return self._measurement_alias

    @property
    def meas_type(self):
        """Return the measurement type, named element_id in Ecad."""
        return self._measurement_type

    @property
    def meas_name(self):
        """Return the measurement name."""
        return self._measurement_name

    @property
    def meas_id(self):
        """Return the measurement id."""
        return self._measurement_id

    @property
    def par_name(self):
        """Return the participant name."""
        return self._participant_name

    @property
    def processed(self):
        """Return a boolean indicating the file has been processed."""
        return self._processed

    def _get_factor_unit(self):
        """Get the unit factor regarding the quality code."""
        res = self.stmt.get_ecad_unit_factor(self._provider_id, self._measurement_type)

        if res:
            self._factor = float(res[0])
            self._unit = res[1]

    def _process(self):
        """Process file and extract relevant data."""
        if self._filepath.exists():
            column_names = [' STAID', '    SOUID', '    DATE', f'   {self._measurement_alias}', f' Q_{self._measurement_alias}']

            # Read the file with measurement data
            df = pd.read_csv(self._filepath, header=13, encoding='ISO-8859-1', usecols=column_names)
            df = df.rename(columns=lambda x: x.strip())

            self._station_id = df['STAID'].iloc[0]
            self._source_id = df['SOUID'].iloc[0]

            first_valid_data_row = df.query(f'Q_{self._measurement_alias} == 0').iloc[0]

            if len(first_valid_data_row):
                start_valid_data_date = first_valid_data_row['DATE']
                # Date is a numpy.int64 type. Convert to datetime
                start_valid_data_date = datetime.strptime(str(start_valid_data_date), '%Y%m%d')
                self._start_valid_data_date = datetime(start_valid_data_date.year, start_valid_data_date.month, start_valid_data_date.day, 0, 0, 0, 0, tzinfo=timezone.utc)

            last_valid_data_row = df.query(f'Q_{self._measurement_alias} == 0').iloc[-1]

            if len(last_valid_data_row):
                end_valid_data_date = last_valid_data_row['DATE']
                # Date is a numpy.int64 type. Convert to datetime
                end_valid_data_date = datetime.strptime(str(end_valid_data_date), '%Y%m%d')
                self._end_valid_data_date = datetime(end_valid_data_date.year, end_valid_data_date.month, end_valid_data_date.day, 0, 0, 0, 0, tzinfo=timezone.utc)

            del df

            self._processed = True
        else:
            current_app.logger.error(f'Source file {self._filepath} does not exist')

    def _get_source_data(self):
        """Get the measurement type and participant from the sources file."""
        sources_path = self._filepath.parent / 'sources.txt'

        if sources_path.exists():
            df = pd.read_csv(sources_path, header=18, encoding='ISO-8859-1')
            df = df.rename(columns=lambda x: x.strip())

            measurement_type = df.loc[df['SOUID'] == self._source_id, 'ELEID'].values[0]

            if measurement_type:
                self._measurement_type = measurement_type.strip()

            participant_name = df.loc[df['SOUID'] == self._source_id, 'PARNAME'].values[0]

            if participant_name:
                self._participant_name = participant_name.strip()

        del df

    def process(self):
        """Preprocess the file."""
        self._process()
        self._get_source_data()
        self._get_factor_unit()

    def read(self):
        """Read the data from file."""
        # Generate the list of dates using pandas date_range function
        # and convert the result to a list of datetime objects
        dates = pd.date_range(self._start_valid_data_date, self._end_valid_data_date, freq='D', tz='UTC').to_pydatetime().tolist()

        # Get measurement's data as pandas dataframe to provide them to the bokeh ColumnDataSource
        # We have to set the value of the y axis to a None value for the days which has no data from some source
        # Set the column names to import
        column_names = ['    DATE', f'   {self._measurement_alias}', f' Q_{self._measurement_alias}']

        # Read the file with measurement data
        df = pd.read_csv(self._filepath, header=13, encoding='ISO-8859-1', usecols=column_names)
        df = df.rename(columns=lambda x: x.strip())

        # Fill the values list with None in all elements of the list
        # The values list has to had equal number of elements than the dates list
        values = [math.nan for i in range(len(dates))]

        # Iterate on data
        for _, row in df.iterrows():
            # Get the date
            meas_date = row['DATE']

            if meas_date:
                # Date is a numpy.int64 type. Convert to datetime
                meas_date = datetime.strptime(str(meas_date), '%Y%m%d')
                meas_date = datetime(meas_date.year, meas_date.month, meas_date.day, 0, 0, 0, 0, tzinfo=timezone.utc)

                # Get only valid data dates
                if meas_date >= self._start_valid_data_date or meas_date <= self._end_valid_data_date:
                    # quality code for TX (0='valid'; 1='suspect'; 9='missing')
                    meas_qual = row[f'Q_{self._measurement_alias}']

                    # Get the value multiplying it by factor. If quality is not zero (meaning valid) or value is -9999, then the resulting value is None
                    val = int(row[self._measurement_alias])
                    meas_value = val * self._factor if int(meas_qual) == 0 else None

                    if meas_value is not None:
                        try:
                            # Get the index of the date in the x axis
                            ind = dates.index(meas_date)

                            # insert the value at the index position
                            values[ind] = meas_value

                            # compute average
                            Average.set_value(meas_date, meas_value)
                        except ValueError:
                            pass

        average = Average.calculate_averages()

        return dates, values, average
