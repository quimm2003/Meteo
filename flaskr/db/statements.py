"""Module with functions to query the database."""
# Created: sáb jul 13 18:14:26 2024 (+0200)
# Last-Updated: dom sep 29 15:18:47 2024 (+0200)
# Filename: statements.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
from db import db


class Statements():
    """Functions to query the database."""

    def __init__(self):
        """Initialize the class."""
        # Get the database connection object
        self._conn = db.get_db()

    def commit(self):
        """Commit insert, update and delete statements."""
        self._conn.commit()

    def get_provider_extra_data(self, provider_id):
        """Get data from providers_extra_data table."""
        extra_data = None

        stmt = 'SELECT key, value FROM providers_extra_data WHERE provider_id = %s'

        with self._conn.cursor() as cur:
            cur.execute(stmt, (provider_id,))
            extra_data = cur.fetchall()

        return extra_data

    def get_providers_data(self):
        """Return all providers data.

        Including its magnitudes and measurements
        """
        providers = None
        providers_data = {}

        with self._conn.cursor() as cur:
            cur.execute('SELECT id, name, description, url, update_data_period, acknowledgment FROM providers')
            providers = cur.fetchall()

        if providers:
            for provider in providers:
                provider_id = provider[0]

                if provider_id is not None:
                    if provider_id not in providers_data:
                        providers_data[provider_id] = {}
                        providers_data[provider_id]['name'] = provider[1]
                        providers_data[provider_id]['description'] = provider[2]
                        providers_data[provider_id]['url'] = provider[3]
                        providers_data[provider_id]['update_data_period'] = provider[4]
                        providers_data[provider_id]['acknowledgment'] = provider[5]

                        extra_data = self.get_provider_extra_data(provider_id)

                        for row in extra_data:
                            providers_data[provider_id][row[0]] = row[1]

                    magnitudes = self.get_magnitude_id_name(provider_id=provider_id)

                    if magnitudes:
                        if 'magnitudes' not in providers_data[provider_id]:
                            providers_data[provider_id]['magnitudes'] = {}

                        for magnitude_id, magnitude_name in magnitudes:
                            providers_data[provider_id]['magnitudes'][magnitude_id] = {}
                            providers_data[provider_id]['magnitudes'][magnitude_id]['name'] = magnitude_name

                            measurements = self.get_measurement_id_name(magnitude_id=magnitude_id)

                            if measurements:
                                if 'measurements' not in providers_data[provider_id]['magnitudes'][magnitude_id]:
                                    providers_data[provider_id]['magnitudes'][magnitude_id]['measurements'] = {}

                                for measurement_id, measurement_name in measurements:
                                    providers_data[provider_id]['magnitudes'][magnitude_id]['measurements'][measurement_id] = measurement_name

        return providers_data

    def get_provider_data_by_station_id(self, data_station_id):
        """Return all providers data.

        Including its magnitudes and measurements
        """
        provider_id = None
        provider = None
        provider_data = {}

        stmt = 'SELECT t1.id, t1.name, t1.description, t1.url, t1.update_data_period, t1acknowledgment FROM providers t1, stations t2 WHERE t2.data_station_id = %s And t1.provider_id = t2.provider_id'

        with self._conn.cursor() as cur:
            cur.execute(stmt, (data_station_id,))
            provider = cur.fetchall()

        if provider:
            provider_id = provider[0]

            if provider_id is not None:
                provider_data[provider_id] = {}
                provider_data[provider_id]['name'] = provider[1]
                provider_data[provider_id]['description'] = provider[2]
                provider_data[provider_id]['url'] = provider[3]
                provider_data[provider_id]['update_data_period'] = provider[4]
                provider_data[provider_id]['acknowledgment'] = provider[5]

                magnitudes = self.get_magnitude_id_name(provider_id=provider_id)

                if magnitudes:
                    provider_data[provider_id]['magnitudes'] = {}

                    for magnitude_id, magnitude_name in magnitudes:
                        provider_data[provider_id]['magnitudes'][magnitude_id] = {}
                        provider_data[provider_id]['magnitudes'][magnitude_id]['name'] = magnitude_name

                        measurements = self.get_measurement_id_name(magnitude_id=magnitude_id)

                        if measurements:
                            provider_data[provider_id]['magnitudes'][magnitude_id]['measurements'] = {}

                            for measurement_id, measurement_name in measurements:
                                provider_data[provider_id]['magnitudes'][magnitude_id]['measurements'][measurement_id] = measurement_name

        return provider_id, provider_data

    def get_provider_id(self, name):
        """Return the id of the provider identified by name.

        :param name: The name of the provider
        :type name: str
        :return: The id of the provider.
        :rtype: int|None
        """
        provider_id = None

        with self._conn.cursor() as cur:
            cur.execute('SELECT id FROM providers WHERE name = %s', (name,))
            result = cur.fetchall()

            if len(result) > 0:
                provider_id = result[0][0]

        return provider_id

    def get_provider_name(self, provider_id):
        """Return the name of the provider identified by its id.

        :param provider_id: The id of the provider
        :type provider_id: int
        :return: The name of the provider.
        :rtype: str|None
        """
        name = None

        with self._conn.cursor() as cur:
            cur.execute('SELECT name FROM providers WHERE id = %s', (provider_id,))
            result = cur.fetchall()

            if len(result) > 0:
                name = result[0][0]

        return name

    def get_provider_update_period(self, provider_id):
        """Return the update data period of the provider identified by provider_id.

        :param provider_id: The id of the provider
        :type provider_id: int
        :return: The update data period.
        :rtype: int|None
        """
        data_period = None

        if provider_id is not None:
            cur = None

            with self._conn.cursor() as cur:
                cur.execute('SELECT update_data_period FROM providers WHERE id = %s', (provider_id,))

                result = cur.fetchall()

                if len(result) > 0:
                    data_period = result[0][0]

        return data_period

    def get_provider_acknowledgement(self, provider_id):
        """Return the provider acknowledgement.

        :param provider_id: the id of the provider.
        :type provider_id: int
        :return: The acknowledgment if any.
        :rytpe: str|None
        """
        acknowledgement = None

        if provider_id is not None:
            cur = None

            with self._conn.cursor() as cur:
                cur.execute('SELECT acknowledgment FROM providers WHERE id = %s', (provider_id,))

                result = cur.fetchall()

                if len(result) > 0:
                    acknowledgement = result[0][0]

        return acknowledgement

    def get_magnitude_id_name(self, provider_id=None, name=None):
        """Return the name of the magnitude (temperature, humidity, etc.).

        The result is returned as a list of tuples in the form (id, name)
        :param provider_id: The id of the provider
        :type provider_id: int
        :param name: The name of the magnitude.
        :type name: str
        :return: a list of tuples containing the id and name of the magnitudes.
        :rtype: list
        """
        res = []

        if provider_id is not None:
            stmt = f'SELECT m.id, m.name FROM magnitudes m, providers_magnitudes pm WHERE m.id = pm.magnitude_id AND pm.provider_id = {provider_id}'

            if name is not None:
                stmt = f'{stmt} AND m.name = \'{name}\''
        elif name is not None:
            stmt = f'SELECT id, name FROM magnitudes WHERE name = \'{name}\''

        with self._conn.cursor() as cur:
            cur.execute(stmt)

            result = cur.fetchall()

            if result:
                for row in result:
                    res.append((row[0], row[1]))

        return res

    def get_magnitude_name(self, provider_id, magnitude_id):
        """Return the name of the magnitude (temperature, humidity, etc.).

        :param provider_id: The id of the provider
        :type provider_id: int
        :param magnitude_id: The id of the magnitude.
        :type magnitude_id: int
        :return: The name of the magnitude.
        :rtype: str|None
        """
        magnitude = None

        stmt = 'SELECT m.name FROM magnitudes m, providers_magnitudes pm WHERE m.id = %s AND m.id = pm.magnitude_id AND pm.provider_id = %s'

        with self._conn.cursor() as cur:
            cur.execute(stmt, (magnitude_id, provider_id))

            result = cur.fetchall()

            if result:
                magnitude = result[0][0]

        return magnitude

    def get_measurement_id_name(self, magnitude_id, name=None):
        """Return the id and the name of the measurements belonging to some magnitude (temperature, humidity, etc.).

        The result is returned as a list of tuples in the form: (id, name)
        :param magnitude_id: The id of the magnitude
        :type magnitude_id: int
        :param name: The name of the measurement.
        :type name: str
        :return: a list of tuples containing the id and name of the measurements.
        :rtype: list
        """
        res = []
        stmt = 'SELECT id, name FROM measurements WHERE magnitude_id = %s'

        if name is not None:
            stmt = f'{stmt} AND name = \'{name}\''

        with self._conn.cursor() as cur:
            cur.execute(stmt, (magnitude_id,))

            result = cur.fetchall()

            if result:
                for row in result:
                    res.append((row[0], row[1]))

        return res

    def get_measurement_last_download(self, magnitude_id, name):
        """Return the last download date of the data belonging to some magnitude (temperature, humidity, etc.).

        :param magnitude_id: The id of the magnitude
        :type magnitude_id: int
        :param name: The name of the measurement.
        :type name: str
        :return: A tuple with the last download and last try dates as strings
        :rtype: tuple|None
        """
        res = None
        stmt = 'SELECT last_download, last_try FROM measurements WHERE magnitude_id = %s AND name = %s'

        with self._conn.cursor() as cur:
            cur.execute(stmt, (magnitude_id, name))

            result = cur.fetchall()

            if result:
                res = (result[0][0], result[0][1])

        return res

    def set_measurement_last_download(self, last_download, magnitude_id, name):
        """Set the last download date of the data belonging to some magnitude (temperature, humidity, etc.).

        :param last_download: the last download date
        :type last_download: datetime
        :param magnitude_id: The id of the magnitude
        :type magnitude_id: int
        :param name: The name of the measurement.
        :type name: str
        :return: The number of rows affected
        :rtype: int
        """
        rowcount = 0
        stmt = 'UPDATE measurements SET last_download = %s WHERE magnitude_id = %s AND name = %s'

        with self._conn.cursor() as cur:
            cur.execute(stmt, (last_download, magnitude_id, name))
            rowcount = cur.rowcount

            if rowcount == 1:
                self.commit()

        return rowcount

    def set_measurement_last_try(self, last_try, magnitude_id, name):
        """Set the last try date of the data belonging to some magnitude (temperature, humidity, etc.).

        :param last_try: the last try date
        :type last_try: datetime
        :param magnitude_id: The id of the magnitude
        :type magnitude_id: int
        :param name: The name of the measurement.
        :type name: str
        :return: The number of rows affected
        :rtype: int
        """
        rowcount = 0
        stmt = 'UPDATE measurements SET last_try = %s WHERE magnitude_id = %s AND name = %s'

        with self._conn.cursor() as cur:
            cur.execute(stmt, (last_try, magnitude_id, name))
            rowcount = cur.rowcount

            if rowcount == 1:
                self.commit()

        return rowcount

    def get_provider_data(self, provider_name):
        """Get the data for a source:  provider_id, magnitudes and measurements.

        :param provider_name: The name of the provider
        :type provider_name: str
        :return: a dict containing the provider, magnitudes and measurements data stored in the database
        :rtype: dict
        """
        data = {}

        provider_id = self.get_provider_id(provider_name)

        if provider_id:
            data['provider_id'] = provider_id

            magnitudes = self.get_magnitude_id_name(provider_id)

            for mg_id, mg_name in magnitudes:
                if 'data' not in data:
                    data['data'] = {}

                data['data'][mg_id] = {}
                data['data'][mg_id]['name'] = mg_name

                measurements = self.get_measurement_id_name(mg_id)

                for me_id, me_name in measurements:
                    if 'measurements' not in data['data'][mg_id]:
                        data['data'][mg_id]['measurements'] = {}

                    data['data'][mg_id]['measurements'][me_id] = me_name

        return data

    def get_data_url(self, provider_id, magnitude_id, measurement_id):
        """Return the url corresponding to the provider, magnitude and measurement.

        :param provider_id: The id of the provider
        :type provider_id: int
        :param magnitude_id: The id of the magnitude
        :type magnitude_id: int
        :param measurement_id: The id of the measurement.
        :type measurement_id: int
        :return: The url to download the corresponding file with data
        :rtype: str
        """
        res = None
        stmt = 'SELECT url FROM data_files WHERE provider_id = %s AND magnitude_id = %s AND measurement_id = %s'

        if provider_id is not None and magnitude_id is not None and measurement_id is not None:
            with self._conn.cursor() as cur:
                cur.execute(stmt, (provider_id, magnitude_id, measurement_id))

                result = cur.fetchall()

                if result:
                    res = result[0][0]

        return res

    def count_stations(self):
        """Count the number of stations stored in the database.

        :return: The number of stations stored in the database.
        :rtype: int
        """
        res = None
        stmt = 'SELECT COUNT(id) FROM stations'

        with self._conn.cursor() as cur:
            cur.execute(stmt)
            result = cur.fetchall()

            res = result[0][0]

        return res

    def check_station(self, provider_id, station_id):
        """Check if a station exists in the database.

        If it exists return the subtypes and the latitude and longitude values to check them.
        :param provider_id: The id of the provider
        :type provider_id: int
        :param station_id: The id of the station
        :type station_id: int
        """
        res = None

        with self._conn.cursor() as cur:
            cur.execute('SELECT lat, lon FROM stations WHERE provider_id = %s AND station_id = %s', (provider_id, station_id))

            result = cur.fetchall()

            res = result[0] if result else None

        return res

    def insert_station(self, provider_id, station_id, name, cn, lat, lon, height):
        """Insert a new station in the stations table.

        :param provider_id: The id of the provider
        :type provider_id: int
        :param station_id: The id of the station
        :type station_id: int
        :param name: The name of the measurement.
        :type name: str
        :param cn: The country code for the station's country
        :type cn: str
        :param lat: The latitude in decimal format
        :type lat: float
        :param lon: The longitude in decimal format
        :type lon: float
        :param height: The height of the station in meters
        :type height: int
        :return: The number of rows affected
        :rtype: int
        """
        rowcount = 0

        with self._conn.cursor() as cur:
            cur.execute('INSERT into stations(provider_id, station_id, name, cn, lat, lon, height) VALUES (%s, %s, %s, %s, %s, %s, %s)', (provider_id, station_id, name, cn, lat, lon, height))
            rowcount = cur.rowcount

            if rowcount == 1:
                self.commit()

        return rowcount

    def get_stations_data(self, provider_id, station_id=None):
        """Get the data from the stations table.

        :param provider_id: The id of the provider
        :type provider_id: int
        :param station_id: The id of the station
        :type station_id: int|None
        :return: All data stored in the database for this station
        :rtype: list|None
        """
        res = None

        stmt = 'SELECT id, station_id, name, cn, lat, lon, height, popup FROM stations WHERE provider_id = %s'

        with self._conn.cursor() as cur:
            if station_id is not None:
                stmt += ' AND station_id = %s'
                cur.execute(stmt, (provider_id, station_id))
            else:
                stmt += ' ORDER BY id'
                cur.execute(stmt, (provider_id,))

            res = cur.fetchall()

        return res

    def get_station_popup(self, station_id):
        """Get the popup info from the stations table.

        :param station_id: The id of the station
        :type station_id: int|None
        :return: the popup for the station
        :rtype: list|None
        """
        res = None

        stmt = 'SELECT popup FROM stations WHERE id = %s'

        with self._conn.cursor() as cur:
            cur.execute(stmt, (station_id,))

            res = cur.fetchall()

        return res

    def get_station_ids_from_staid(self, provider_id, staid):
        """Get the id (auto increment from database table) and the station_id (from provider) from stations given its station_id and provider_id.

        :param provider_id: The id of the provider
        :type provider_id: int
        :param staid: The id of the station as per provider.
        :type station_id: int|None
        :return: a list containing tuples with id, station_id data
        :rtype: list|None
        """
        res = None

        stmt = 'SELECT id, station_id FROM stations WHERE provider_id = %s AND station_id = %s'

        with self._conn.cursor() as cur:
            cur.execute(stmt, (provider_id, staid))
            res = cur.fetchall()

        return res

    def get_station_provider(self, station_id):
        """Get the station's provider id and name.

        :param station_id: The id of the station in the table
        :type station_id: int
        :return: The provider id and name
        :rtype: tuple
        """
        provider_id = None
        provider_name = None

        stmt = 'SELECT t1.provider_id, t2.name FROM stations t1, providers t2 WHERE t1.id = %s AND t1.id = t2.id'

        with self._conn.cursor() as cur:
            cur.execute(stmt, (station_id,))
            res = cur.fetchall()

            if res:
                provider_id = res[0][0]
                provider_name = res[0][1]

        return provider_id, provider_name

    def check_ecad_source(self, provider_id, magnitude_id, measurement_id, source_id):
        """Check if a source exists in the database.

        If it exists return the latitude and longitude values to check them.
        """
        res = None

        with self._conn.cursor() as cur:
            cur.execute('SELECT id, data_station_id FROM ecad_sources WHERE provider_id = %s AND magnitude_id = %s AND measurement_id = %s AND source_id = %s', (provider_id, magnitude_id, measurement_id, source_id))

            result = cur.fetchall()

            res = (result[0][0], result[0][1]) if result else None

        return res

    def insert_source(self, provider_id, magnitude_id, measurement_id, data_station_id, souid, souname, element_id, start_date, stop_date, participant_id, participant_name):
        """Insert a new source in the ecad_sources table."""
        rowcount = 0
        lastrowid = None

        with self._conn.cursor() as cur:
            cur.execute('INSERT INTO ecad_sources (provider_id, magnitude_id, measurement_id, data_station_id, source_id, source_name, element_id, start_date, end_date, participant_id, participant_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (provider_id, magnitude_id, measurement_id, data_station_id, souid, souname, element_id, start_date, stop_date, participant_id, participant_name))
            rowcount = cur.rowcount

            if rowcount == 1:
                self.commit()

                lastrowid = cur.lastrowid

        return rowcount, lastrowid

    def count_ecad_sources(self):
        """Count the number of sources stored in the database."""
        res = None
        stmt = 'SELECT COUNT(id) FROM ecad_sources'

        with self._conn.cursor() as cur:
            cur.execute(stmt)
            result = cur.fetchall()

            res = result[0][0]

        return res

    def get_ecad_source_data_by_data_station_id(self, data_station_id):
        """Get the source data using the station id serial field."""
        res = None
        stmt = 'SELECT magnitude_id, measurement_id, element_id, start_date, end_date, participant_name, source_id, id FROM ecad_sources WHERE data_station_id = %s'

        with self._conn.cursor() as cur:
            cur.execute(stmt, (data_station_id,))
            res = cur.fetchall()

        return res

    def get_ecad_data_by_data_station_id(self, data_station_id):
        """Get the station data using the station id serial field."""
        res = None
        rowcount = 0

        stmt = 'SELECT t1.magnitude_id, t1.measurement_id, t1.element_id, t1.start_date, t1.end_date, t1.participant_name, t1.source_id, t1.id, t2.name, t3.name, t5.factor FROM ecad_sources t1, magnitudes t2, measurements t3, stations t4, ecad_elements t5 WHERE t1.data_station_id = t4.id AND t4.id = %s AND t1.magnitude_id = t2.id AND t1.measurement_id = t3.id AND t5.provider_id = t1.provider_id AND t5.magnitude_id = t1.magnitude_id AND t5.measurement_id = t1.measurement_id AND t1.element_id = t5.element_id'

        with self._conn.cursor() as cur:
            cur.execute(stmt, (data_station_id,))
            res = cur.fetchall()
            rowcount = cur.rowcount

        return res, rowcount

    def update_source_popup_marker(self, popup, data_station_id):
        """Update the source popup in the station table.

        :param popup: The popup data to be updated.
        :type popup: str
        :param data_station_id: The id of the station in the table
        :type data_station_id: int
        :return: the number of rows affected and the new row id
        :rtype: tuple
        """
        rowcount = 0
        lastrowid = None

        if popup:
            with self._conn.cursor() as cur:
                cur.execute('UPDATE stations SET popup = %s WHERE id = %s', (popup, data_station_id))
                rowcount = cur.rowcount

                if rowcount == 1:
                    self.commit()

                    lastrowid = cur.lastrowid

        return rowcount, lastrowid

    def get_source_eleid_from_station_id(self, provider_id, staid, measurement_id, magnitude_id):
        """Get the element_id from source by station_id and measurement_id.

        :param provider_id: The id of the provider
        :type provider_id: int
        :param staid: The id of the station as per provider.
        :type station_id: int|None
        :param measurement_id: The id of the measurement.
        :type measurement_id: int
        :param magnitude_id: The id of the magnitude
        :type magnitude_id: int
        """
        data = {}

        if provider_id and staid:
            stmt = 'SELECT t1.id, t1.element_id, t1.start_date, t1.end_date FROM ecad_sources t1, stations t2 WHERE t1.data_station_id = t2.id AND t2.provider_id = %s AND t2.id = %s AND t1.measurement_id = %s AND t1.magnitude_id = %s'

            with self._conn.cursor() as cur:
                cur.execute(stmt, (provider_id, staid, measurement_id, magnitude_id))
                res = cur.fetchall()

                if cur.rowcount == 1:
                    data['souid'] = res[0][0]
                    data['eleid'] = res[0][1]
                    data['start'] = res[0][2]
                    data['end'] = res[0][3]

        return data

    def update_ecad_source_element(self, souid, souname, element_id, start_date, stop_date, participant_id, participant_name, existing_source_id):
        """Update source using the source with preferred element."""
        rowcount = 0

        with self._conn.cursor() as cur:
            cur.execute('UPDATE ecad_sources SET source_id = %s, source_name = %s, element_id = %s, start_date = %s, end_date = %s, participant_id = %s, participant_name = %s WHERE id = %s', (souid, souname, element_id, start_date, stop_date, participant_id, participant_name, existing_source_id))

            rowcount = cur.rowcount

            if rowcount == 1:
                self.commit()

        return rowcount

    def count_ecad_elements(self):
        """Count the number of rows in ecad_elements table.

        :return: The number of rows in ecad_elements table.
        :rtype: int
        """
        res = 0

        with self._conn.cursor() as cur:
            cur.execute('SELECT count(*) FROM ecad_elements')
            result = cur.fetchall()

            res = result[0][0]

        return res

    def get_ecad_element(self, provider_id, magnitude_id, measurement_id, eleid):
        """Get the element's data from database.

        :param provider_id: The id of the provider
        :type provider_id: int
        :param magnitude_id: The id of the magnitude
        :type magnitude_id: int
        :param measurement_id: The id of the measurement.
        :type measurement_id: int
        :param eleid: The name of the element
        :type eleid: str
        :return: The data associated with the element.
        :rtype: list|None
        """
        res = None

        with self._conn.cursor() as cur:
            cur.execute('SELECT element_id, description, unit, factor FROM ecad_elements WHERE provider_id = %s AND magnitude_id = %s AND measurement_id = %s AND element_id = %s', (provider_id, magnitude_id, measurement_id, eleid))
            res = cur.fetchall()

        return res

    def insert_ecad_element(self, provider_id, magnitude_id, measurement_id, eleid, descr, unit, factor, priority):
        """Insert the element's data.

        :param provider_id: The id of the provider
        :type provider_id: int
        :param magnitude_id: The id of the magnitude
        :type magnitude_id: int
        :param measurement_id: The id of the measurement.
        :type measurement_id: int
        :param eleid: The name of the element
        :type eleid: str
        :param descr: The description of the element
        :type descr: str
        :param unit: The unit used in the sources using this element
        :type unit: str
        :param factor: The factor which is used to multiply the data on the sources using this element
        :type factor: float
        :param priority: The priority of the element id in order to use one or another.
        :type priority: int
        :return: the number of rows affected and the new row id
        :rtype: tuple
        """
        rowcount = 0
        lastrowid = None

        with self._conn.cursor() as cur:
            cur.execute('INSERT INTO ecad_elements (provider_id, magnitude_id, measurement_id, element_id, description, unit, factor, priority) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', (provider_id, magnitude_id, measurement_id, eleid, descr, unit, factor, priority))
            rowcount = cur.rowcount

            if rowcount == 1:
                self.commit()

                lastrowid = cur.lastrowid

        return rowcount, lastrowid

    def get_ecad_unit_factor(self, provider_id, element_id):
        """Get unit and factor from ecad_elements table by provider and element id.

        :param provider_id: the id of the data provider
        :type provider_id: int
        :param element_id: the id of the element which is unique in the table.
        :type element_id: str
        :return: The factor and unit for this element.
        :rtype: list|None
        """
        res = None

        stmt = 'SELECT factor, unit FROM ecad_elements WHERE provider_id = %s AND element_id = %s'

        with self._conn.cursor() as cur:
            cur.execute(stmt, (provider_id, element_id))
            result = cur.fetchall()

            if result:
                res = result[0]

        return res

    def get_preferred_measurements_type(self):
        """Get the element ids ordered by priority.

        :return: Dictionary with priority lists by measurement.
        :rtype: dict
        """
        res = {}

        stmt = 'SELECT t2.name, t1.element_id FROM ecad_elements t1, measurements t2 WHERE t1.measurement_id = t2.id ORDER BY t1.measurement_id, t1.priority'

        with self._conn.cursor() as cur:
            cur.execute(stmt)
            result = cur.fetchall()

            if result:
                for measurement, element_id in result:
                    if measurement not in res:
                        res[measurement] = []

                    res[measurement].append(element_id)

        return res
