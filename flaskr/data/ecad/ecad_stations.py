#!/usr/bin/python3
"""Class to manage all data regarding meteorological stations."""
# Created: vie jul 19 13:29:08 2024 (+0200)
# Last-Updated: sáb nov  8 17:51:06 2025 (+0100)
# Filename: ecad_stations.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
from db.statements import Statements

from flask import current_app, url_for

import pandas as pd


class EcadStations():
    """Class to manage all data regarding meteorological stations."""

    def __init__(self, provider_id, provider_data, stations_filename=None, measurement=None):
        """Initialize the class.

        :param stations_filename: path to the file containing the station data.
        :type stations_filename: pathlib.Path
        :param provider_id: the id of the provider which offers the station data
        :type provicer_id: int
        :measurement: the type of the station measurement data. For example, for temperature the stations measures the max, min and mean temperatures.
        :type measurement: str
        """
        self.provider_id = provider_id
        self.provider_data = provider_data
        self.stations_filename = stations_filename
        self.measurement = measurement
        self.magnitudes = self.provider_data['magnitudes']
        self.stmt = Statements()

    def dms_to_dd(self, dms: str) -> int:
        """Convert degrees, minutes, seconds to decimal.

        :param dms: string containing the degrees, minutes and seconds in the format: degrees:minutes:seconds
        :type dms: str
        :returns: The decimal translation of the degrees, minutes and seconds value.
        :rtype: float
        """
        dms = dms.strip()
        dms_split = dms.split(':')

        deg_str = dms_split[0]
        deg = float(dms_split[0])
        minu = float(dms_split[1])
        sec = float(dms_split[2])

        if deg_str[0] == '-':
            minu = -1 * minu
            sec = -1 * sec

        dd = deg + minu / 60 + sec / 3600

        return dd

    def save_data(self):
        """Save the data from the station to the database."""
        if self.stations_filename.exists():
            df = pd.read_csv(self.stations_filename, header=13, encoding='UTF-8')
            df = df.rename(columns=lambda x: x.strip())

            if df is not None:
                df = df.reset_index()

                for _, row in df.iterrows():
                    staid = row['STAID']
                    staname = row['STANAME'].strip()
                    cn = row['CN'].strip()
                    dmslat = row['LAT'].strip()
                    dmslon = row['LON'].strip()
                    height = row['HGHT']

                    # Convert dms to dec
                    lat = self.dms_to_dd(dmslat)
                    lon = self.dms_to_dd(dmslon)

                    station_data = self.stmt.check_station(self.provider_id, staid)

                    if not station_data:
                        self.stmt.insert_station(self.provider_id, staid, staname, cn, lat, lon, height)
        else:
            current_app.logger.error(f'stations filename {self.stations_filename} does not exist')

    def _get_marker_source_data(self, ecad_source_files):
        """Extract source information to place it in the marker information shown when marker gets clicked.

        :param ecad_source_files: dictionary containing instances of EcadSourceFile for each measurement.
        :type source_data: dict
        :returns: The source info to be placed into the marker info. It contains html labels and entities.
        :rtype: str
        """
        info = None
        source_info = {}

        # magnitude_id, measurement_id, element_id, start_date, end_date, participant_name

        keys = list(ecad_source_files)
        keys.sort()

        for key in keys:
            ecad_source_file = ecad_source_files[key]

            magnitude_id = ecad_source_file.magnitude_id
            measurement_id = ecad_source_file.meas_id
            start_date = ecad_source_file.start
            end_date = ecad_source_file.end

            magnitude_name = self.magnitudes[magnitude_id]['name'] if magnitude_id in self.magnitudes else None

            if magnitude_name:
                if magnitude_id not in source_info:
                    source_info[magnitude_id] = {}
                    source_info[magnitude_id]['name'] = magnitude_name

                measurements = self.magnitudes[magnitude_id]['measurements']

                if measurements is not None:
                    if 'measurements' not in source_info[magnitude_id]:
                        source_info[magnitude_id]['measurements'] = {}

                    for dict_measurement_id, measurement_name in measurements.items():
                        if dict_measurement_id == measurement_id:
                            source_info[magnitude_id]['measurements'][measurement_id] = (measurement_name, start_date, end_date)
                            break

        if source_info:
            info = '<br/>Magnitudes:<br/>'

            for magnitude_id in source_info.keys():
                info += f'- {source_info[magnitude_id]["name"]}'

                for measurement in source_info[magnitude_id]['measurements'].values():
                    info += f'<br/>&nbsp;&nbsp;{measurement[0]}: {measurement[1]} to: {measurement[2]}'

        return info

    def save_source_popup_markers(self, source_files):
        """Create marker's popups and save them to the database.

        :param source_files: instance of EcadSourceFiles
        :type source_files: EcadSourceFiles
        """
        stations = self.stmt.get_stations_data(self.provider_id)

        for row in stations:
            data_station_id = row[0]
            station_id = row[1]
            staname = row[2].replace("'", "\'")
            cn = row[3]
            height = row[6]

            ecad_source_files = source_files.get_source_files(station_id)

            if ecad_source_files:
                source_popup = self._get_marker_source_data(ecad_source_files)

                url = f'/station/{data_station_id}'
                anchor = f'<a class="popup-button" href="{url}">Show Station Data</a>'

                popup = f'Station: {data_station_id} - {staname} - {cn} - Height: {height}<br/>{source_popup}<br/><br/>{anchor}'

                self.stmt.update_source_popup_marker(popup, data_station_id)
