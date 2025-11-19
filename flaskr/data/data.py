#!/usr/bin/python3
"""Base class for data with common methods and common info."""
# Created: sáb jul  6 18:31:59 2024 (+0200)
# Last-Updated: sáb nov  8 19:14:39 2025 (+0100)
# Filename: download_data.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
from data.ecad.ecad import Ecad

from db.statements import Statements

from flask import current_app


class Data:
    """Base class for data with common methods and common info."""

    def __init__(self) -> None:
        """Initialize the class."""
        self.providers = None
        self.tmp_data_dir = current_app.config['TMP_DATA_LOCATION']
        self.curr_data_dir = current_app.config['CURRENT_DATA_LOCATION']
        self.curr_graph_dir = current_app.config['CURRENT_GRAPH_FILES_LOCATION']
        self.tmp_graph_dir = current_app.config['TMP_GRAPH_FILES_LOCATION']

    def _get_provider_instance(self, provider_id, provider_data):
        """Initialize provider instance.

        :param provider_id: the id of the provider
        :type provider_id: int
        :param provider_data: a dictionary containing the provider's data
        :type provider_data: dict
        """
        prov_inst = None

        if provider_data['name'] == 'ecad':
            prov_inst = Ecad(provider_id, provider_data)

        return prov_inst

    def _add_directories_paths(self, provider_data):
        """Add the app directories paths to provider_data.

        :param provider_data: a dictionary containing the provider's data
        :type provider_data: dict
        """
        provider_data['dirs'] = {}
        provider_data['dirs']['tmp_data_dir'] = self.tmp_data_dir
        provider_data['dirs']['curr_data_dir'] = self.curr_data_dir
        provider_data['dirs']['curr_graph_dir'] = self.curr_graph_dir
        provider_data['dirs']['tmp_graph_dir'] = self.tmp_graph_dir

    def _get_provider_data(self, provider_id):
        """Get a provider's data.

        :param provider_id: the id of the provider
        :type provider_id: int
        """
        provider_data = None

        if provider_id in self.providers.keys():
            provider_data = self.providers[provider_id]
            self._add_directories_paths(provider_data)

        return provider_data

    def _get_provider_data_by_station_id(self, data_station_id):
        """Get provider data from database using the station's id.

        :param data_station_id: the id of the station in the database table
        :type data_station_id: int
        """
        provider_id = None
        provider_data = None

        if data_station_id:
            stmt = Statements()

            provider_id, provider_data = stmt.get_provider_data_bystation_id(data_station_id)

        return provider_id, provider_data

    def initialize_providers(self):
        """Get providers info from the database."""
        stmt = Statements()

        self.providers = stmt.get_providers_data()

    def handle_data(self):
        """Initialize the providers instances for each provider."""
        for provider_id in self.providers.keys():
            provider_data = self._get_provider_data(provider_id)

            prov_inst = self._get_provider_instance(provider_id, provider_data)
            prov_inst.handle_data()

    def get_station_data(self, data_station_id):
        """Get station data.

        This is a Flask route.
        :param data_station_id: the id of the station in the database table
        :type data_station_id: int
        """
        provider_id, provider_data = self._get_provider_data_by_station_id(data_station_id)
        self._add_directories_paths(provider_data)

        prov_inst = self._get_provider_instance(provider_id, provider_data)

        return prov_inst.get_station_data(data_station_id)

    def get_station_popup(self, data_station_id):
        """Get station popup.

        This is a Flask route.
        :param data_station_id: the id of the station in the database table
        :type data_station_id: int
        """
        stmt = Statements()

        return stmt.get_station_popup(data_station_id)

    def get_stations_markers(self):
        """Build a dict containing the information to place a marker in the map, including its popup and css class name.

        The info is retrieved from the stations database table.

        :returns: a dict of list per provider containing the markers to be placed into the map.
        :rtype: list
        """
        stmt = Statements()

        st_markers = {}

        for provider_id in self.providers.keys():
            stations = stmt.get_stations_data(provider_id)

            if stations:
                for row in stations:
                    data_staid = row[0]
                    station_name = row[2]
                    country = row[3]
                    lat = row[4]
                    lon = row[5]
                    popup = row[7]

                    # Derive a clean text tooltip (no HTML, no None)
                    if popup:
                        # Use only the header part before the first <br to avoid long HTML content
                        header = str(popup).split('<br', 1)[0]
                        tooltip = header
                        popup_html = f'<br />{popup}'
                    else:
                        # Fallback to a simple, human-readable tooltip
                        if station_name:
                            tooltip = f'{station_name} ({country})'
                        else:
                            tooltip = f'Station {data_staid}'
                        popup_html = f'<br />{tooltip}'

                    marker = {
                        'lat': lat,
                        'lon': lon,
                        'popup': popup_html,
                        'tooltip': tooltip,
                        'station_id': f'{data_staid}',
                        'provider_id': f'{provider_id}',
                        'country': country
                    }

                    if provider_id not in st_markers:
                        st_markers[provider_id] = []

                    st_markers[provider_id].append(marker)

        return st_markers

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
