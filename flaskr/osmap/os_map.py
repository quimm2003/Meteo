#!/usr/bin/python3
"""Initialize the Flask Blueprint which will show the OpenStreet map into the browser."""
# Created: sáb jul  6 18:13:02 2024 (+0200)
# Last-Updated: dom nov 17 18:08:27 2024 (+0100)
# Filename: os_map.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
from flask import Blueprint, render_template, request
from db.statements import Statements
from country_list import countries_for_language


# Supported UI languages
SUPPORTED_LANGUAGES = ("en", "es")

# Simple translation dictionary for UI strings
TRANSLATIONS = {
    "en": {
        "title": "Meteorological Data from Stations",
        "language_label": "Language:",
        "provider_label": "Provider:",
        "provider_placeholder": "-- Select Provider --",
        "country_label": "Country:",
        "country_placeholder": "-- Select Country --",
        "show_map": "Show Map",
        "update_map": "Update Map",
    },
    "es": {
        "title": "Datos meteorológicos de estaciones",
        "language_label": "Idioma:",
        "provider_label": "Proveedor:",
        "provider_placeholder": "-- Selecciona proveedor --",
        "country_label": "País:",
        "country_placeholder": "-- Selecciona país --",
        "show_map": "Mostrar mapa",
        "update_map": "Actualizar mapa",
    },
}


class OSMap():
    """Shows the OpenStreet Map."""

    def __init__(self, markers=None, providers=None):
        """Initialize the class."""
        self.bp = Blueprint('osmap', __name__, url_prefix='/')
        self.bp.add_url_rule('/', view_func=self.show_map)
        self.markers = markers if markers else [{'lat': 0, 'lon': 0, 'popup': 'This is the middle of the map.'}]
        self.providers = providers if providers else {}

    def _get_language(self) -> str:
        """Determine the current UI language from the request.

        Priority: query parameter ?lang= → default to 'en'.
        """
        lang = (request.args.get("lang") or "en").lower()
        if lang not in SUPPORTED_LANGUAGES:
            lang = "en"
        return lang

    def _get_available_countries(self, lang: str):
        """Get list of countries that have stations in the database.
        
        :param lang: Language code (e.g. 'en', 'es') for country names
        :type lang: str
        :return: A list of tuples (country_code, country_name) sorted by name
        :rtype: list
        """
        stmt = Statements()

        # Fallback to English if the requested language is not supported
        language_for_countries = lang if lang in {"en", "es"} else "en"
        countries_dict = dict(countries_for_language(language_for_countries))
        available_countries = []
        
        # Get distinct country codes from stations table
        with stmt._conn.cursor() as cur:
            cur.execute('SELECT DISTINCT cn FROM stations ORDER BY cn')
            country_codes = [row[0] for row in cur.fetchall()]
        
        # Map country codes to names
        for code in country_codes:
            name = countries_dict.get(code, code)
            available_countries.append((code, name))
        
        # Sort by country name
        available_countries.sort(key=lambda x: x[1])
        
        return available_countries

    def show_map(self):
        """Render the map."""
        lang = self._get_language()
        countries = self._get_available_countries(lang)
        texts = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        return render_template(
            'index.html',
            markers=self.markers,
            providers=self.providers,
            countries=countries,
            lang=lang,
            texts=texts,
        )
