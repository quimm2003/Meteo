"""Facade class to the classes handling Ecad data."""
# Created: vie jul 12 09:08:29 2024 (+0200)
# Last-Updated: sáb nov  8 18:40:25 2025 (+0100)
# Filename: ecad_data.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
from data.ecad.ecad_get_data import EcadGetData
from data.ecad.ecad_save_data import EcadSaveData
from graphs.ecad.ecad_graphs import EcadGraphs


class Ecad():
    """Facade class to handle Ecad data."""

    def __init__(self, provider_id, provider_data):
        """Initialize class."""
        self.provider_id = provider_id
        self.provider = provider_data['name']
        self.provider_data = provider_data
        self.update_data_period = self.provider_data['update_data_period']
        self.magnitudes = self.provider_data['magnitudes']
        self.source_files = None

    def _get_data(self):
        """Download data, if needed, from Ecad site.

        :return: a boolean (need_to_save) which informs if there is something to save.
        And a dictionary (what_to_save) with information about what has to be saved.
        :rytpe: tuple(bool, dict)
        """
        ecad_get_data = EcadGetData(self.provider_id, self.provider_data)
        need_to_save, what_to_save = ecad_get_data.get_data()

        return need_to_save, what_to_save

    def _save_data(self, what_to_save):
        """Save data to the database."""
        ecad_save_data = EcadSaveData(self.provider_id, self.provider_data, self)
        self.source_files = ecad_save_data.save_data(what_to_save)

    def _generate_stations_html_graphs(self):
        """Generate the stations graphs as html files."""
        ecad_graphs = EcadGraphs(self.provider_id, self.provider_data)
        return ecad_graphs.generate_stations_html_graphs(self.source_files)

    def handle_data(self):
        """Handle the Ecad datasets."""
        need_to_save, what_to_save = self._get_data()

        # if need_to_save:
        if True:
            self._save_data(what_to_save)
            self._generate_stations_html_graphs()
