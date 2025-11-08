#!/usr/bin/python3
"""Module to configure the Flask application."""
# Created: sáb jul  6 12:46:59 2024 (+0200)
# Last-Updated: mié sep 18 12:12:45 2024 (+0200)
# Filename: config.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
from pathlib import Path

from flask import current_app


class Config:
    """App configuration class."""

    @property
    def CURRENT_DATA_LOCATION(self):
        """The path to the current data being used.

        :return: The path to the current data directory.
        :rtype: Path
        """
        curr_data_loc = Path(current_app.root_path).joinpath('data/current').resolve()

        if not curr_data_loc.exists():
            try:
                curr_data_loc.mkdir(parents=True)
            except FileExistsError:
                pass

        return curr_data_loc

    @property
    def TMP_DATA_LOCATION(self):
        """The path to the temprary directory to work with data.

        :return: The path to the temporary data directory.
        :rtype: Path
        """
        tmp_data_loc = Path(current_app.root_path).joinpath('data/tmp').resolve()

        if not tmp_data_loc.exists():
            try:
                tmp_data_loc.mkdir(parents=True)
            except FileExistsError:
                pass

        return tmp_data_loc.resolve()

    @property
    def CURRENT_GRAPH_FILES_LOCATION(self):
        """The path to the directory holding static html files being used.

        :return: The path to the current graph fiels directory.
        :rtype: Path
        """
        current_graph_files_loc = Path(current_app.root_path).joinpath('graphs/current').resolve()

        if not current_graph_files_loc.exists():
            try:
                current_graph_files_loc.mkdir(parents=True)
            except FileExistsError:
                pass

        return current_graph_files_loc

    @property
    def TMP_GRAPH_FILES_LOCATION(self):
        """The path to the temporary directory to work with static html files.

        :return: The path to the temporary graph fiels directory.
        :rtype: Path
        """
        tmp_graph_files_loc = Path(current_app.root_path).joinpath('graphs/tmp').resolve()

        if not tmp_graph_files_loc.exists():
            try:
                tmp_graph_files_loc.mkdir(parents=True)
            except FileExistsError:
                pass

        return tmp_graph_files_loc

    @property
    def DATABASE(self):
        """The database name.

        :return: the database name.
        :rtype: str
        """
        dbname = 'meteo'

        return dbname

    @property
    def DB_HOST(self):
        """The database host name.

        :return: the database host name.
        :rtype: str
        """
        dbhost = 'localhost'

        return dbhost

    @property
    def DB_USER(self):
        """The database usernname.

        :return: the database user name.
        :rtype: str
        """
        dbuser = 'meteo'

        return dbuser

    @property
    def DB_PASSWORD(self):
        """The database password.

        :return: the database password.
        :rtype: str
        """
        dbpassword = 'meteo'

        return dbpassword

    @property
    def LOG_FILE(self):
        """The log file path.

        :return: the log file path.
        :rtype: Path
        """
        return Path(current_app.root_path).joinpath('logs/app.log')
