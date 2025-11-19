#!/usr/bin/python3
"""Module to save the Ecad elements into the database."""
# Created: lun ago  5 07:26:27 2024 (+0200)
# Last-Updated: sáb nov  8 18:09:57 2025 (+0100)
# Filename: ecad_elements.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
from db.statements import Statements

import pandas as pd


class EcadElements():
    """Class to store the Ecad Elements into the database."""

    def __init__(self, ecad_instance, elements_filename, magnitude_id, measurement_id):
        """Initialize the class."""
        self.ecad = ecad_instance
        self.elements_filename = elements_filename
        self.magnitude_id = magnitude_id
        self.measurement_id = measurement_id

        self.preferred_measurements_type = {
            'max': ['TX21', 'TX14', 'TX2', 'TX3', 'TX12', 'TX13', 'TX15', 'TX16', 'TX17', 'TX18', 'TX19', 'TX20', 'TX5', 'TX6', 'TX8', 'TX10', 'TX7', 'TX9', 'TX11', 'TX1'],
            'mean': ['TG24', 'TG21', 'TG22', 'TG20', 'TG15', 'TG17', 'TG18', 'TG12', 'TG13', 'TG14', 'TG19', 'TG16', 'TG6', 'TG7', 'TG8', 'TG10', 'TG3', 'TG9', 'TG11', 'TG23', 'TG5', 'TG1'],
            'min': ['TN19', 'TN13', 'TN2', 'TN3', 'TN11', 'TN12', 'TN14', 'TN15', 'TN16', 'TN17', 'TN18', 'TN5', 'TN6', 'TN8', 'TN9', 'TN10', 'TN1']
        }

        self.stmt = Statements()

    def _get_unit_factor(self, factor_unit):
        """Get the unit and factor from string.

        :param factor_unit: string containing the factor and unit to be splitted.
        :type factor_unit: str
        :return: tuple with unit and factor.
        :rtype: tuple
        """
        unit = None
        factor = None

        if factor_unit:
            a_factor_unit = factor_unit.split()
            if a_factor_unit:
                factor = float(a_factor_unit[0])

                if 'C' in a_factor_unit[1]:
                    unit = 'C'

        return unit, factor

    def _check_element(self, eleid):
        """Check if the element exists in the database.

        :param eleid: the id of the element as stated by Ecad
        :type eleid: str
        :return: True if the element exists; False otherwise
        :rtype: boolean
        """
        res = False

        element = self.stmt.get_ecad_element(self.ecad.provider_id, self.magnitude_id, self.measurement_id, eleid)

        if element and element[0][0] == eleid:
            res = True

        return res

    def _set_priority(self, eleid):
        """Set the priority of the element id in the database.

        :param eleid: the element id.
        :type eleid: str
        """
        priority = None

        if self.measurement_id in self.ecad.magnitudes[self.magnitude_id]['measurements']:
            measurement = self.ecad.magnitudes[self.magnitude_id]['measurements'][self.measurement_id]

            if measurement in self.preferred_measurements_type:
                if eleid in self.preferred_measurements_type[measurement]:
                    priority = self.preferred_measurements_type[measurement].index(eleid)

        return priority

    def save_data(self):
        """Save elements into the database."""
        if self.elements_filename.exists():
            # The description contains commas, so we can not read the file as csv
            colspecs = [(0, 5), (6, 156), (158, 169)]
            df = pd.read_fwf(self.elements_filename, header=10, encoding='ISO-8859-1', colspecs=colspecs, index_column=0)

            if df is not None:
                df = df.reset_index()

                for _, row in df.iterrows():
                    eleid = row.iloc[1].strip()
                    descr = row.iloc[2].strip()
                    factor_unit = row.iloc[3]

                    unit, factor = self._get_unit_factor(factor_unit)

                    priority = self._set_priority(eleid)

                    if self._check_element(eleid) is False:
                        self.stmt.insert_ecad_element(self.ecad.provider_id, self.magnitude_id, self.measurement_id, eleid, descr, unit, factor, priority)
