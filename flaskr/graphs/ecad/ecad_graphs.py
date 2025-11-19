#!/usr/bin/python3
"""Class to generate the html files with interactive graphs."""
# Created: lun ago 19 18:41:47 2024 (+0200)
# Last-Updated: mar nov 18 09:00:22 2025 (+0100)
# Filename: ecad_graphs.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
import math
import os

from data.averages import Average
from db.statements import Statements
from flask import current_app
from graphs.graphs import Graphs
import pandas as pd
from tqdm import tqdm


class EcadGraphs(Graphs):
    """Class to generate the html files with interactive graphs."""

    def __init__(self, provider_id, provider_data):
        """Initialize the class."""
        self.provider_id = provider_id
        self.provider_data = provider_data
        self.provider = self.provider_data['name']
        self.acknowledgement = self.provider_data['acknowledgment']
        self.provider_data_dir = self.provider_data['dirs']['curr_data_dir'] / self.provider
        self.max_temp_dir = self.provider_data_dir / 'temperature' / 'max'
        self.min_temp_dir = self.provider_data_dir / 'temperature' / 'min'
        self.mean_temp_dir = self.provider_data_dir / 'temperature' / 'mean'

        self.ecad_measurements_translations = {
            'es': {
                'mean': 'Media',
                'max': 'Máxima',
                'min': 'Mínima'
            }
        }

        Graphs.__init__(self)

    def _generate_list_of_dates(self, sources):
        """Generate a list with all dates, which will be the x axis.

        :param sources: the list of sources related to the station
        :type sources: list
        """
        # Get the max and min date from sources.
        min_date = None
        max_date = None

        for row_source in sources:
            start_date = row_source[3]
            end_date = row_source[4]

            if min_date is None or start_date < min_date:
                min_date = start_date

            if max_date is None or end_date > max_date:
                max_date = end_date

        # Generate the list of dates using pandas date_range function
        # and convert the result to a list of datetime objects
        return pd.date_range(min_date, max_date, freq='D', tz='UTC').to_pydatetime().tolist()

    def _trim_invalid_values(self, data_dict):
        """Get rid of x_axis items that does not have values.

        :param data_dict: dictionary with data to be trimmed.
        :type data_dict: dict
        """
        # Get a list of the data_dict keys
        dict_keys = list(data_dict)
        dict_keys.remove('x_axis')

        # Build a list of lists
        lol = [data_dict[x] for x in dict_keys]

        # List of bad indexes
        bad_indexes = []

        # Check elements value
        for ind in range(len(lol[0])):
            if all(math.isnan(lst[ind]) for lst in lol):
                bad_indexes.append(ind)
            else:
                if bad_indexes and bad_indexes[-1] != -1:
                    # Signal the start of valid data with a -1
                    bad_indexes.append(-1)

        # Build a list with the indexes to remove
        indexes_to_remove = []

        if bad_indexes:
            first_ind = None
            last_ind = None

            try:
                first_ind = bad_indexes.index(-1)
                last_ind = len(bad_indexes) - bad_indexes[::-1].index(-1) - 1
            except ValueError:
                pass

            if first_ind is not None:
                indexes_to_remove = bad_indexes[0:first_ind]

            if last_ind is not None:
                indexes_to_remove += bad_indexes[last_ind + 1:]

            if first_ind is None and last_ind is None:
                indexes_to_remove = bad_indexes

        # Trim start and end bad indexes, but not the ones between valid data
        if indexes_to_remove:
            rev_indexes_to_remove = sorted(indexes_to_remove, reverse=True)

            for index in rev_indexes_to_remove:
                for column in list(data_dict):
                    del data_dict[column][index]

        return data_dict

    def _compute_decade(self, meas_date):
        """Calculate the decade which meas_date is in.

        :param meas_date: The datetime to calculate the decade.
        :type meas_date: datetime
        """
        year = meas_date.year

        return year - (year % 10)

    def _generate_station_data_dict(self, ecad_source_files):
        """Generate Panda's dataframe from station sources.

        :param ecad_source_files: dictionary with data for each measurement.
        :type ecad_source_files: dict
        :returns: a dictionary with the x axis dates and the y axis lists with data.
        :rtype: dict
        """
        # Initialize averages
        Average.initialize()

        # dates is our x axis
        data_dict = {'x_axis': None}

        # Legend list
        legend = []

        measurements = list(ecad_source_files)

        for idx, measurement in enumerate(measurements):
            ecad_file = ecad_source_files[measurement]

            # Set legend
            meas = self.ecad_measurements_translations['es'][measurement]
            legend.append(meas)

            # Graph line name
            graph_line_name = self.graph_lines_names[idx]

            # Read file
            dates, values, meas_average = ecad_file.read()

            # Set x axis
            if data_dict['x_axis'] is None:
                data_dict['x_axis'] = dates

            # Set EcadSourceFile average to the average dict
            Average.merge_measurement_averages(meas_average, graph_line_name)

            # Store the list of values in the data_dict using the y axis names
            data_dict[graph_line_name] = values

        # Ensure that the average dict meets the Bokeh plots requirements
        average = Average.normalize_averages()

        return data_dict, legend, average

    def generate_stations_html_graphs(self, source_files):
        """Generate the stations graphs as html files.

        :param source_files: The EcadSourceFiles instance object.
        :type source_files: EcadSourceFiles
        """
        current_app.logger.info(f"{self.provider.title()}: Generating stations static html graph files.")
        stmt = Statements()

        current_graph_dir = self.provider_data['dirs']['curr_graph_dir'] / self.provider
        temp_graph_dir = self.provider_data['dirs']['tmp_graph_dir'] / self.provider

        # Get the stations data
        stations = stmt.get_stations_data(self.provider_id)

        if stations:
            # Set the progress bar
            num_graph_files = len(os.listdir(current_graph_dir))
            num_meas_files = max(len(os.listdir(self.max_temp_dir)), len(os.listdir(self.min_temp_dir)), len(os.listdir(self.mean_temp_dir)))

            num_files_left = num_meas_files - num_graph_files
            progress_bar = tqdm(range(num_files_left), file=open(os.devnull, 'w'))

            for row in stations:
                data_staid = row[0]
                station_id = row[1]

                html_file_name = current_graph_dir / f'STA_{data_staid}.html'

                if not html_file_name.exists():
                    # Get the sources related to the station
                    ecad_source_files = source_files.get_source_files(station_id)

                    if ecad_source_files:
                        # Generate the data dictionary to be used by bokeh
                        data_dict, legend, average = self._generate_station_data_dict(ecad_source_files)

                        if data_dict:
                            # create html file with bokeh
                            self.create_html_file(data_dict, legend, row, average, current_graph_dir, temp_graph_dir)

                            # Update progress and print in log
                            progress_bar.update()
                            current_app.logger.info(str(progress_bar))
