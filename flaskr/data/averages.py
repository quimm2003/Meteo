#!/usr/bin/python3
"""Module to handle the averages for each measurement."""
# Created: dom sep 22 13:39:25 2024 (+0200)
# Last-Updated:
# Filename: ecad_average.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
import math


class Average():
    """Class to handle the Ecad data averages."""

    # Averages per decade and per measurement
    averages = {}

    # Averages per decade for one measurement
    average = {}

    def __init__(self):
        """Initialize the class."""

    @classmethod
    def initialize(cls):
        """Initialize the class attributes."""
        cls.averages = {}
        cls.average = {}

    @classmethod
    def _compute_decade(cls, meas_date):
        """Get the decade corresponding to meas_date.

        :param meas_date: the date from which the decade will be computed
        :type meas_date: datetime
        :return: The decade which the meas_date is in.
        :rtype: int
        """
        year = meas_date.year

        decade = year - (year % 10)

        return decade

    @classmethod
    def set_value(cls, meas_date, meas_value):
        """Add a value to the dictionary."""
        decade = cls._compute_decade(meas_date)

        if decade not in cls.average:
            cls.average[decade] = {'value': 0, 'count': 0, 'average': None}

        cls.average[decade]['value'] += meas_value
        cls.average[decade]['count'] += 1

    @classmethod
    def calculate_averages(cls):
        """Calculate the average of all data processed."""
        for decade in cls.average.keys():
            if cls.average[decade]['count'] > 0:
                mean = float(cls.average[decade]['value']) / cls.average[decade]['count']
                cls.average[decade]['average'] = round(math.ceil(mean * 100) / 100, 2)
            else:
                cls.average[decade]['average'] = math.nan

        return cls.average

    @classmethod
    def merge_measurement_averages(cls, meas_average, graph_line_name):
        """Merge the averages of the different measurements.

        Set the measurement average into the average dict.

        :param meas_average: The averages dict from the EcadSourceFile.
        :type meas_average: dict
        :param graph_line_name: The name of the line in the graph.
        :type graph_line_name: str
        """
        for decade, data in meas_average.items():
            if 'average' in data:
                if data['average'] is not None:
                    if decade not in cls.averages:
                        cls.averages[decade] = {}

                    if graph_line_name not in cls.averages[decade]:
                        cls.averages[decade][graph_line_name] = {}

                    cls.averages[decade][graph_line_name]['average'] = data['average']

    @classmethod
    def normalize_averages(cls):
        """Normalize the decades and measurements values on the dictionary.

        It has to meet the Bokeh plots requirements.
        """
        # Calculate the max number of lines per decade
        max_lines = 0
        dec = 0

        decades = list(cls.averages)

        for decade in decades:
            mx_lines = max(len(cls.averages[decade].keys()), max_lines)
            if mx_lines > max_lines:
                max_lines = mx_lines
                dec = decade

        line_names = list(cls.averages[dec].keys())

        # If a decade does not has max_lines, delete it from the dictionary
        for decade in decades:
            keys = cls.averages[decade].keys()

            if len(keys) < max_lines:
                missing_lines = [item for item in line_names if item not in keys]

                for miss_line in missing_lines:
                    cls.averages[decade][miss_line] = {'average': math.nan}

        return cls.averages

    @classmethod
    def get_average_tooltips_line_name(cls, averages):
        """Get the line with max decades without math.nan value."""
        decades = list(averages)
        line_name = None
        min_nan_counts = None
        min_line = None

        for decade in decades:
            nan_counts = 0

            lines = list(averages[decade])
            lines.sort()

            for line in lines:
                if averages[decade][line]['average'] == math.nan:
                    nan_counts += 1

            if min_nan_counts is None:
                min_nan_counts = nan_counts
                min_line = line
            else:
                if nan_counts < min_nan_counts:
                    min_line = line

            if nan_counts == 0:
                line_name = line
                break

        if line_name is None:
            line_name = min_line

        return line_name

    @classmethod
    def generate_average_tooltips(cls, averages, legend):
        """Generate the tooltips to be shown in the average graph."""
        tooltips = []

        tooltips.append(("Década", "@x_axis"))

        decades = list(averages)

        for decade in decades:
            keys = list(averages[decade])

            for index, value in enumerate(keys):
                legend_name = legend[index].capitalize()
                tooltips.append((f'{legend_name}', str(averages[decade][value]['average'])))

        return tooltips
