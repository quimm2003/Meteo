#!/usr/bin/python3
"""Module to save Ecad data into the database."""
# Created: dom sep 22 12:53:18 2024 (+0200)
# Last-Updated:
# Filename: ecad_save_data.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
import pickle
import time
from datetime import datetime, timedelta

from data.ecad.ecad_elements import EcadElements
from data.ecad.ecad_handle_data import EcadHandleData
from data.ecad.ecad_source_files import EcadSourceFiles
from data.ecad.ecad_stations import EcadStations

from db.statements import Statements

from flask import current_app


class EcadSaveData(EcadHandleData):
    """Class to save Ecad data to the database."""

    def __init__(self, provider_id, provider_data):
        """Initialize the class."""
        self.provider_id = provider_id
        self.provider_data = provider_data
        self.provider = self.provider_data['name']
        self.magnitudes = self.provider_data['magnitudes']
        self.sources_pickle_file_name = self.provider_data['sources_pickle_file_name']
        self.ecad_date_filename = self.provider_data['ecad_date_file_name']
        self.current_data_dir = self.provider_data['dirs']['curr_data_dir'] / self.provider
        self.pickle_file = None
        self.source_files = None

        EcadHandleData.__init__(self, self.provider_data)

        self.stmt = Statements()

    def _serialize_unserialize_sources(self, curr_file_date):
        """Serialize source files if not done before. Unserialize it if already done.

        :param curr_file_date: string representing the current data files update from Ecad.
        :type curr_file_date: str
        """
        source_files = None

        curr_date = datetime.strptime(curr_file_date, '%d-%m-%Y')

        self.pickle_file = self.current_data_dir / f'{curr_date.strftime("%Y_%m_%d")}_{self.sources_pickle_file_name}'

        if self.pickle_file.exists():
            current_app.logger.info(f'{self.provider.title()}: Loading data from {self.pickle_file}.')
            with open(self.pickle_file, 'rb') as pick:
                source_files = pickle.load(pick)
        else:
            source_files = EcadSourceFiles()
            source_files.parse_source_data_files()

            current_app.logger.info(f'{self.provider.title()}: Dumping data to {self.pickle_file}.')
            with open(self.pickle_file, 'wb') as pick:
                pickle.dump(source_files, pick, protocol=pickle.HIGHEST_PROTOCOL)

        self.source_files = source_files

    def save_data(self, what_to_save):
        """Save Ecad data."""
        curr_file_date = None

        if self.current_data_dir.exists():
            for magnitude_id in self.magnitudes.keys():
                magnitude = self.magnitudes[magnitude_id]['name']

                for measurement_id, measurement in self.magnitudes[magnitude_id]['measurements'].items():
                    stations_filename = self.current_data_dir / magnitude / measurement / 'stations.txt'
                    elements_filename = self.current_data_dir / magnitude / measurement / 'elements.txt'

                    if curr_file_date is None:
                        curr_file_date = self.get_ecad_data_timestamp(self.current_data_dir / magnitude / measurement / self.ecad_date_filename)

                    if self.provider in what_to_save and magnitude_id in what_to_save[self.provider] and measurement in what_to_save[self.provider][magnitude_id]:
                        # Save stations first
                        if what_to_save[self.provider][magnitude_id][measurement]['stations'] is True:
                            if stations_filename.exists():
                                current_app.logger.info(f'{self.provider.title()} {magnitude} {measurement}: Saving Stations')

                                ecad_stations = EcadStations(self.provider_id, self.provider_data, stations_filename=stations_filename, measurement=measurement)
                                ecad_stations.save_data()
                            else:
                                current_app.logger.error(f"stations filename {stations_filename} does not exist.")

                        # Save elements
                        if what_to_save[self.provider][magnitude_id][measurement]['elements'] is True:
                            if elements_filename.exists():
                                measurement_values = self.stmt.get_measurement_id_name(magnitude_id, measurement)
                                measurement_id = measurement_values[0][0]

                                current_app.logger.info(f'{self.provider.title()} {magnitude} {measurement}: Saving Elements')

                                ecad_elements = EcadElements(self.ecad, elements_filename, magnitude_id, measurement_id)
                                ecad_elements.save_data()

                # Process sources
                # if what_to_save[self.provider]['sources'] is True:
                if True:
                    current_app.logger.info(f'{self.provider.title()}: Parsing source files.')

                    t1 = time.time()

                    self._serialize_unserialize_sources(curr_file_date)

                    t2 = time.time()
                    current_app.logger.info(f'{self.provider.title()}: {self.source_files.num_files_processed} files processed, {self.source_files.num_files_added} files added. Elapsed time: {timedelta(seconds=t2-t1)}')

                    # current_app.logger.info(f'{self.provider.title()}: Saving source popup markers')
                    # ecad_stations = EcadStations(self.provider_id, self.provider_data)
                    # ecad_stations.save_source_popup_markers(self.source_files)

        return self.source_files
