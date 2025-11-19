#!/usr/bin/python3
"""Handle a collection of EcadSourceFile objects."""
# Created: jue sep 12 10:27:01 2024 (+0200)
# Last-Updated: sáb nov  8 19:43:25 2025 (+0100)
# Filename: ecad_source_files.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
from data.ecad.ecad_source_file import EcadSourceFile
from db.statements import Statements
from flask import current_app


class EcadSourceFiles():
    """Class to handle a collection of EcadSourceFile objects.

    - Parses all ecad source files.
    - Decides what data files to use for each station.
    - Saves source's data into the database (ecad_sources)
    - Saves the relationship between stations and ecad_sources to the database (stations_ecad_sources)
    """

    def __init__(self, provider_id, provider_data):
        """Initialize class."""
        self.provider_id = provider_id
        self.provider_data = provider_data
        self.magnitudes = self.provider_data['magnitudes']
        self.current_data_dir = self.provider_data['dirs']['curr_data_dir'] / self.provider_data['name']

        self.ecad_measurements_aliases = {
            'mean': 'TG',
            'max': 'TX',
            'min': 'TN'
        }

        self.station_source_files = {}

        self.num_files_processed = 0
        self.num_files_added = 0

        self.stmt = Statements()

        self.preferred_measurements_type = self.stmt.get_preferred_measurements_type()

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

    def _filter_sources(self, source_file, measurement):
        """Filter sources regarding its methods to calculate measurements.

        :param source_file: instance of EcadSourceFile to be filtered.
        :type source_file: EcadSourceFile
        :param measurement: the measurement's type name
        :type measurement: str
        """
        result = True

        if source_file.station_id in self.station_source_files and source_file.meas_name in self.station_source_files:
            other_source = self.station_source_files[source_file.station_id][source_file.meas_name]

            meas_list = self.preferred_measurements_type[measurement]

            curr = None
            if source_file.meas_type in meas_list:
                curr = meas_list.index(source_file.meas_type)

            other = None
            if other_source.meas_type in meas_list:
                other = meas_list.index(other_source.meas_type)

            if curr and other and curr >= other:
                result = False

        return result

    def _normalize_dates(self, ecad_source_files):
        """Ensure start and end dates of each EcadSourceFile are equal.

        We need to do this because all graph lines has to have the same amount of data.
        :param ecad_source_files: dictionary with data for each measurement.
        :type ecad_source_files: dict
        """
        date_start = None
        date_end = None
        measurements = list(ecad_source_files)

        for measurement in measurements:
            ecad_file = ecad_source_files[measurement]

            if ecad_file.start:
                if date_start is None:
                    date_start = ecad_file.start
                else:
                    date_start = max(date_start, ecad_file.start)

            if ecad_file.end:
                if date_end is None:
                    date_end = ecad_file.end
                else:
                    date_end = max(date_end, ecad_file.end)

        if date_start is not None:
            for measurement in measurements:
                ecad_file = ecad_source_files[measurement]
                ecad_file.start = date_start

        if date_end is not None:
            for measurement in measurements:
                ecad_file = ecad_source_files[measurement]
                ecad_file.end = date_end

    def get_source_files(self, station_id):
        """Get the instances of EcadSourceFiles for station id.

        :param station_id: the provider's id for the station.
        :type station_id: int
        :return: A dict containing the EcadSourceFile instances for each measurement.
        :rtype: dict
        """
        ecad_source_files = None

        if station_id in self.station_source_files:
            ecad_source_files = self.station_source_files[station_id]
            self._normalize_dates(ecad_source_files)

        return ecad_source_files

    def _add_source(self, source_file):
        """Add EcadSourceFile to dictionary.

        :param source_file: The EcadSourceFile instance to be added.
        :type source_file: EcadSourceFile
        """
        if source_file.station_id not in self.station_source_files:
            self.station_source_files[source_file.station_id] = {}

        self.station_source_files[source_file.station_id][source_file.meas_name] = source_file
        self.num_files_added += 1

    def parse_source_data_files(self):
        """Parse all source data files for ecad."""

        if self.current_data_dir.exists():
            for magnitude_id in self.magnitudes.keys():
                magnitude = self.magnitudes[magnitude_id]['name']

                for measurement_id, measurement in self.magnitudes[magnitude_id]['measurements'].items():
                    data_dir = self.current_data_dir / magnitude / measurement

                    meas_alias = self.ecad_measurements_aliases[measurement]

                    files = data_dir.glob(f'{meas_alias}_*.txt')

                    for filepath in files:
                        source_file = EcadSourceFile(self.provider_id, filepath, magnitude_id, (measurement_id, measurement, meas_alias))

                        if source_file:
                            source_file.process()

                            if source_file.processed:
                                if self._filter_sources(source_file, measurement):
                                    self._add_source(source_file)

                            self.num_files_processed += 1
