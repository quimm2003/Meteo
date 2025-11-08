#!/usr/bin/python3
"""The Flask app."""
# Created: sáb jul  6 11:11:48 2024 (+0200)
# Last-Updated: lun nov 25 12:57:48 2024 (+0100)
# Filename: main.py
# Author: Joaquin Moncanut <quimm2003@gmail.es>

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import click

from data.data import Data

from db import db

from flask import Flask

from osmap.os_map import OSMap


def configure_logging(app):
    """Configure handlers and loggers.

    :param app: The Flask app
    :type app: flask
    """
    # Eliminamos los posibles manejadores, si existen, del logger por defecto
    del app.logger.handlers[:]

    # Añadimos el logger por defecto a la lista de loggers
    loggers = [app.logger, ]
    handlers = []

    # Creamos un manejador para escribir los mensajes por consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(verbose_formatter())
    handlers.append(console_handler)

    # Configure a file handler
    file_handler = RotatingFileHandler(filename=app.config['LOG_FILE'], maxBytes=500000, backupCount=2)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(verbose_formatter())
    handlers.append(file_handler)

    # Asociamos cada uno de los handlers a cada uno de los loggers
    for logger in loggers:
        for handler in handlers:
            logger.addHandler(handler)
        logger.propagate = False
        logger.setLevel(logging.DEBUG)


def verbose_formatter():
    """Set the formatter for the loggers.

    :return: a configured formatter
    :rtype: logging.Formatter
    """
    return logging.Formatter(
        '[%(asctime)s] %(levelname)s %(message)s [%(module)s.%(funcName)s:%(lineno)d]',
        datefmt='%Y/%m/%d %H:%M:%S'
    )


def create_app():
    """Configure the Factory function to create the Flask app."""
    # Check if we only want to initialize the database
    init_db = True if 'init-db' in sys.argv else False

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    # import pdb; pdb.set_trace()

    from config.config import Config

    with app.app_context():
        app.config.from_object(Config())
        configure_logging(app)

        # ensure the instance folder exists
        try:
            os.makedirs(app.instance_path)
        except OSError:
            pass

        # Routes
        @app.route('/station/<station_id>', methods=['GET'])
        def station(station_id):
            data = Data()
            return data.get_station_data(station_id)

        @app.route('/popup/<station_id>', methods=['GET'])
        def popup(station_id):
            data = Data()
            return data.get_station_popup(station_id)

        @app.route('/stationsmarkers', methods=['GET'])
        def stations_markers():
            data = Data()
            data.initialize_providers()
            return data.get_stations_markers()

        if init_db:
            # Register database commands
            db.init_app(app)
        else:
            data = Data()
            data.initialize_providers()

            # To put in a separate thread
            # data.handle_data()
            # End to put in a separate thread

            # Get the stations locations and info
            all_stations_markers = data.get_stations_markers()

            # Instantiate Map
            osmap = OSMap(markers=all_stations_markers)
            app.register_blueprint(osmap.bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run()
