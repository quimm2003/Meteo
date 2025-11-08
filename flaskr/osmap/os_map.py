#!/usr/bin/python3
"""Initialize the Flask Blueprint which will show the OpenStreet map into the browser."""
# Created: sáb jul  6 18:13:02 2024 (+0200)
# Last-Updated: dom nov 17 18:08:27 2024 (+0100)
# Filename: os_map.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
from flask import Blueprint, render_template


class OSMap():
    """Shows the OpenStreet Map."""

    def __init__(self, markers=None):
        """Initialize the class."""
        self.bp = Blueprint('osmap', __name__, url_prefix='/')
        self.bp.add_url_rule('/', view_func=self.show_map)
        self.markers = markers if markers else [{'lat': 0, 'lon': 0, 'popup': 'This is the middle of the map.'}]

    def show_map(self):
        """Render the map."""
        return render_template('index.html', markers=self.markers)
