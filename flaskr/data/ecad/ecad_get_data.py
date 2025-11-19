#!/usr/bin/python3
"""Module to download and handle data from Ecad sources."""
# Created: dom sep 22 12:34:46 2024 (+0200)
# Last-Updated:
# Filename: ecad_get_data.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
import shutil
from datetime import datetime
from pathlib import Path
from urllib import request
from zipfile import ZipFile

from data.ecad.ecad_handle_data import EcadHandleData
from db.statements import Statements
from flask import current_app


class EcadGetData(EcadHandleData):
    """Class which handles the download and disposition of Ecad data."""

    def __init__(self, provider_id, provider_data):
        """Initialize class."""
        self.provider_id = provider_id
        self.provider_data = provider_data
        self.provider = self.provider_data['name']
        self.magnitudes = self.provider_data['magnitudes']
        self.current_data_dir = self.provider_data['dirs']['curr_data_dir'] / self.provider
        self.temp_data_dir = self.provider_data['dirs']['tmp_data_dir'] / self.provider
        self.ecad_date_filename = self.provider_data['ecad_date_file_name']

        EcadHandleData.__init__(self, self.provider_data)

        self.stmt = Statements()

        self.file_paths = {}

        self.today = datetime.now()
        self.valid_update_days = (1, 15)

    def _build_filenames(self):
        """Build the filenames."""
        for magnitude_id in self.magnitudes.keys():
            magnitude = self.magnitudes[magnitude_id]['name']

            curr_data_dir = self.current_data_dir / magnitude
            if not curr_data_dir.exists():
                curr_data_dir.mkdir()

            tmp_data_dir = self.temp_data_dir / magnitude
            if not tmp_data_dir.exists():
                tmp_data_dir.mkdir()

            for measurement_id, measurement in self.magnitudes[magnitude_id]['measurements'].items():
                url = self.stmt.get_data_url(self.provider_id, magnitude_id, measurement_id)
                date_url = self.stmt.get_date_url(self.provider_id, magnitude_id, measurement_id)

                if url:
                    # Store url to download the new file
                    if magnitude not in self.file_paths:
                        self.file_paths[magnitude] = {}

                    if measurement not in self.file_paths[magnitude]:
                        self.file_paths[magnitude][measurement] = {}

                    self.file_paths[magnitude][measurement]['url'] = url

                    if date_url:
                        self.file_paths[magnitude][measurement]['date_url'] = date_url

                    # Build the new tmp filename
                    data_suffix = Path(url).suffix

                    # Name of the new downloaded file
                    if 'data' not in self.file_paths[magnitude][measurement]:
                        self.file_paths[magnitude][measurement]['data'] = {'tmp': '', 'curr': ''}

                    self.file_paths[magnitude][measurement]['data']['tmp'] = tmp_data_dir / f'{self.today.strftime("%Y%m%d")}_{self.provider}_{magnitude}_{measurement}{data_suffix}'

                    # Get the current data date filename if it exists
                    self.file_paths[magnitude][measurement]['data']['curr'] = curr_data_dir / self.ecad_date_filename

                    # Path of the file containing generation date
                    if 'date' not in self.file_paths[magnitude][measurement]:
                        self.file_paths[magnitude][measurement]['date'] = {'tmp': ''}

                    self.file_paths[magnitude][measurement]['date']['tmp'] = tmp_data_dir / f'{self.today.strftime("%Y%m%d")}_{self.provider}_{magnitude}_{measurement}{data_suffix}'

    def _check_downloaded_files_date(self, tmp_date, magnitude_id, measurement_id):
        """Check if the last updated date is the same as in the downloaded files.

        If it is the same date, we already have this data.
        """
        update_data = False

        stmt = Statements()
        last_update_data = stmt.get_data_file_updated_date(self.provider_id, magnitude_id, measurement_id)

        if last_update_data:
            delta = tmp_date - datetime(last_update_data.year, last_update_data.month, last_update_data.day)

            if delta.days > 0:
                update_data = True
                stmt.set_data_file_updated_date(tmp_date, self.provider_id, magnitude_id, measurement_id)
        else:
            update_data = True

        return update_data

    def _check_database_data(self, magnitude_id, measurement, what_to_save):
        """Check if database tables for ecad has data.

        If some tables have no data, we have to load it to the database.
        """
        need_to_save = False

        # Check if the data is stored into the database
        res_stations = self.stmt.count_stations()
        res_elements = self.stmt.count_ecad_elements()

        if res_stations == 0 or res_elements == 0:
            need_to_save = True
            now = datetime.now().strftime('%d-%m-%Y')
            self.stmt.set_measurement_last_try(now, magnitude_id, measurement)

            what = ''

            if res_stations == 0:
                what += 'Stations'

            if res_elements == 0:
                what += 'Elements' if len(what) == 0 else ", Elements"

            current_app.logger.warning(f'Data not stored: {what}')

        what_to_save = self._prepare_what_to_save(what_to_save, magnitude_id, measurement)

        what_to_save[self.provider][magnitude_id][measurement]['stations'] = (res_stations == 0)
        what_to_save[self.provider][magnitude_id][measurement]['elements'] = (res_elements == 0)

        return need_to_save, what_to_save

    def _prepare_what_to_save(self, what_to_save=None, magnitude_id=None, measurement=None, value=False):
        """Prepare the dictionary used to inform what data has to be saved."""
        if what_to_save is None:
            what_to_save = {}

        if self.provider not in what_to_save:
            what_to_save[self.provider] = {}

        if magnitude_id is not None and magnitude_id not in what_to_save[self.provider]:
            what_to_save[self.provider][magnitude_id] = {}

        if measurement is not None and measurement not in what_to_save[self.provider][magnitude_id]:
            what_to_save[self.provider][magnitude_id][measurement] = {}

        # Set the value
        if magnitude_id and measurement:
            what_to_save[self.provider][magnitude_id][measurement]['stations'] = value
            what_to_save[self.provider][magnitude_id][measurement]['elements'] = value

        return what_to_save

    def _download_data(self, magnitude_id, measurement):
        """Download files from ECAD."""
        magnitude = self.magnitudes[magnitude_id]['name']

        data_url = self.file_paths[magnitude][measurement]['url']
        tmp_data_filename = self.file_paths[magnitude][measurement]['data']['tmp']

        # Download data
        current_app.logger.info(f"{self.provider.title()} {magnitude} {measurement}: Downloading Data")
        request.urlretrieve(data_url, tmp_data_filename)

        return tmp_data_filename

    def _download_date_file(self, magnitude_id, measurement):
        """Download files from ECAD."""
        magnitude = self.magnitudes[magnitude_id]['name']

        date_url = self.file_paths[magnitude][measurement]['date_url']
        tmp_date_filename = self.file_paths[magnitude][measurement]['date']['tmp']

        # Download data
        current_app.logger.info(f"{self.provider.title()} {magnitude} {measurement}: Downloading Data")
        request.urlretrieve(date_url, tmp_date_filename)

        return tmp_date_filename

    def _extract_data(self, magnitude_id, measurement_id, measurement, tmp_file_date, tmp_data_filename):
        """Extract downloaded data."""
        magnitude = self.magnitudes[magnitude_id]['name']

        # Delete the current data directory
        curr_data_dir = self.current_data_dir / magnitude / measurement

        if curr_data_dir.exists():
            shutil.rmtree(str(curr_data_dir))

        # Extract new data
        if not curr_data_dir.exists():
            curr_data_dir.mkdir(parents=True)

        with ZipFile(tmp_data_filename) as zipf:
            current_app.logger.info(f"{self.provider.title()} {magnitude} {measurement}: Extracting data from zip file")
            zipf.extractall(curr_data_dir)
            self.stmt.set_measurement_last_download(tmp_file_date, magnitude_id, measurement)

        what_to_save = self._prepare_what_to_save(magnitude_id=magnitude_id, measurement=measurement, value=True)

        # Delete the tmp file after it has been extracted
        tmp_data_filename.unlink()

        return what_to_save

    def get_data(self):
        """Download and arrange data files."""
        need_to_save = False
        what_to_save = self._prepare_what_to_save()

        if current_app.config['DOWNLOAD_DATA']:
            self._build_filenames()

            for magnitude_id in self.magnitudes.keys():
                magnitude = self.magnitudes[magnitude_id]['name']

                for measurement_id, measurement in self.magnitudes[magnitude_id]['measurements'].items():
                    # Get new files date
                    tmp_date_filename = self._download_date_file(magnitude_id, measurement)
                    tmp_file_date = self.get_ecad_data_timestamp(tmp_date_filename)
                    tmp_date = datetime.strptime(tmp_file_date, '%d-%m-%Y')

                    # Check if the new files date is the same as the current files date
                    if self._check_downloaded_files_date(tmp_date, magnitude_id, measurement_id):
                        need_to_save = True
                        tmp_data_filename = self._download_data(magnitude_id, measurement)

                        # Get current files date
                        curr_date = None

                        if self.file_paths[magnitude][measurement]['data']['curr'].exists():
                            curr_file_date = self.get_ecad_data_timestamp(self.file_paths[magnitude][measurement]['data']['curr'])
                            curr_date = datetime.strptime(curr_file_date, '%d-%m-%Y')

                            # Extract the zip file if there is no current data or it is obsolete
                            if curr_date is None or curr_date < tmp_date:
                                what_to_save = self._extract_data(magnitude_id, measurement_id, measurement, tmp_file_date, tmp_data_filename)
                            else:
                                # Delete the tmp file as it is the same as the current data
                                tmp_data_filename.unlink()
                    else:
                        current_app.logger.info('Abort: the new files are the same as the current files.')
                        # Delete the tmp file as it is the same as the current data
                        tmp_data_filename.unlink()

                        now = datetime.now().strftime('%d-%m-%Y')
                        self.stmt.set_measurement_last_try(now, magnitude_id, measurement)

                        need_to_save, what_to_save = self._check_database_data(magnitude_id, measurement, what_to_save)
        else:
            for magnitude_id in self.magnitudes.keys():
                magnitude = self.magnitudes[magnitude_id]['name']

                for measurement_id, measurement in self.magnitudes[magnitude_id]['measurements'].items():
                    current_app.logger.info(f"{self.provider.title()} {magnitude} {measurement}: Download cancelled in config")
                    need_to_save, what_to_save = self._check_database_data(magnitude_id, measurement, what_to_save)

        return need_to_save, what_to_save
