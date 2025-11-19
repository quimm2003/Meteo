#!/usr/bin/python3
"""Module with common functions to some Ecad classes."""
# Created: dom sep 22 14:21:47 2024 (+0200)
# Last-Updated:
# Filename: ecad_handle_data.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
import re
from pathlib import Path
from zipfile import ZipFile
from flask import current_app


class EcadHandleData():
    """Class with common functions to some Ecad classes."""

    def __init__(self, provider_data):
        """Initialize the class."""
        self.provider_data = provider_data
        self.ecad_date_filename = self.provider_data['ecad_date_file_name']

    def _extract_date(self, text):
        """Extract date from file."""
        file_date = None

        if text:
            matc = re.search(r'([0-3][0-9]-(0[1-9]|1[0-2])-[0-9]{4})', str(text))

            if matc.lastindex is not None:
                file_date = matc.group(1)

        return file_date

    def get_ecad_data_timestamp(self, data_filename):
        """Extract the publication data timestamp from its file."""
        file_date = None

        # Uncompress file if needed
        pat = Path(data_filename)

        if pat.exists():
            if pat.suffix == '.zip':
                with ZipFile(data_filename) as zipf:
                    with zipf.open(self.ecad_date_filename) as datef:
                        text = datef.readline()
                        file_date = self._extract_date(text)
            else:
                with open(data_filename) as datef:
                    text = datef.readline()
                    file_date = self._extract_date(text)
        else:
            current_app.logger.error("File %s does not exists", data_filename)

        return file_date
