#!/usr/bin/python3
"""Base class for all graph classes."""
# Created: sáb ago 31 09:46:25 2024 (+0200)
# Last-Updated: mié oct  2 23:31:36 2024 (+0200)
# Filename: graphs.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
import math

from bokeh.embed import file_html
from bokeh.models import ColumnDataSource, HoverTool, Legend, Title
from bokeh.models import CrosshairTool, Grid, LinearAxis, SingleIntervalTicker, Span
from bokeh.plotting import curdoc, figure
from bokeh.resources import CDN
from country_list import countries_for_language
from data.averages import Average


class Graphs():
    """Base class for all graph classes."""

    def __init__(self) -> None:
        """Initialize the class."""
        self.graph_lines_names = [chr(x) for x in range(97, 123)]
        self.graph_lines_colors = ['red', 'blue', 'green', 'black', '#00ffff', '#8a2be2', '#42280E', '#7fff00', '#006400', '#8b008b', '#ff8c00', '#ff1493', '#ffd700', '#808080', '#550000', '#808000', '#DA70D6', '#800080', '#008080', '#ff6347', '#ee82ee', '#a0522d ', '#272840']

        # Countries in spanish
        self.es_countries = dict(countries_for_language('es'))

    def _dd_to_dms(self, dd, lat_or_lon):
        """Convert decimal to degrees, minutes, seconds.

        :param dd: the decimal number to be converted
        :type dd: float
        :param lat_or_lon: to identify if we are converting the latitude or the longitude. Values: 'lat', 'lon'.
        :type lat_or_lon: str
        """
        appendix = None

        latitude = ['N', 'S']
        longitude = ['E', 'W']

        # The degrees are the integger part
        deg = int(dd)

        if lat_or_lon == 'lat':
            appendix = latitude[0] if deg > 0 else latitude[1]
        else:
            appendix = longitude[0] if deg > 0 else longitude[1]

        # The minutes and seconds are obtained multiplying the decimal part by 60
        dec = dd - deg
        min = dec * 60
        minutes = int(min)

        sec = int((min - minutes) * 60)

        dms = f'{deg:02}:{minutes:02}:{sec:02}'

        if appendix is not None:
            dms += f' {appendix}'

        return dms

    def get_country_in_spanish(self, cn):
        """Get the station country translated to spanish.

        :param cn: The alpha_2 string representing the country.
        :type cn: str
        """
        return self.es_countries[cn.upper()] if cn else None

    def _configure_main_graph(self, dict_keys, station_data, bok_data, legend):
        """Configure the main graph to plot into the html file."""
        station_id = station_data[1]
        station_name = station_data[2].capitalize()
        cn = station_data[3]
        lat = station_data[4]
        lon = station_data[5]
        height = station_data[6]
        country = self.get_country_in_spanish(cn)

        # Adapted code from https://docs.bokeh.org/en/latest/docs/user_guide/topics/timeseries.html RangeTool
        # Normal graph
        lat = self._dd_to_dms(float(lat), 'lat')
        lon = self._dd_to_dms(float(lon), 'lon')

        date_start = bok_data.data['x_axis'][0].strftime('%d/%m/%Y')
        date_end = bok_data.data['x_axis'][-1].strftime('%d/%m/%Y')

        title = f'Estación: {station_id} - {station_name}, {country} - Latitud: {lat} - Longitud: {lon} - Altura: {height} msnm. Desde {date_start} hasta {date_end}.'

        maing = figure(tools=["xpan", "xwheel_zoom"], toolbar_location=None, name="maing", active_scroll="xwheel_zoom",
                       x_axis_type="datetime", x_axis_location="above", width_policy="max",
                       background_fill_color="#efefef", title=title)

        line = None
        legend_items = []
        tooltips = []
        tooltips.append(("Date:", "@x_axis{%d/%m/%Y}"))
        renderers = []

        # For each y axis list of data, plot a line
        for ind, y_name in enumerate(dict_keys):
            line = maing.line('x_axis', y_name, source=bok_data, line_color=self.graph_lines_colors[ind])

            legend_items.append((legend[ind], [line]))

            format_y = f"@{y_name}"
            format_y += '{0.0} ºC'
            legend_name = legend[ind].capitalize()
            tooltips.append((f"{legend_name}:", format_y))

        renderers.append(line)

        maing.add_tools(HoverTool(tooltips=tooltips, renderers=renderers, formatters={"@x_axis": "datetime"}, mode="vline"))

        width = Span(dimension="width", line_width=1)
        height = Span(dimension="height", line_width=1)
        maing.add_tools(CrosshairTool(overlay=[width, height]))

        lines_legend = Legend(items=legend_items, location="center")
        maing.add_layout(lines_legend, 'right')

        # Set the y axis label
        maing.yaxis.axis_label = 'Temperatura ºC'

        # Plot horizontal lines in grid
        maing.ygrid.grid_line_alpha = 0.5
        maing.ygrid.grid_line_color = 'gray'

        acknowledgement = self.provider_data['acknowledgment']

        if acknowledgement:
            maing.add_layout(Title(text=acknowledgement, align="center", text_align="center", text_font_style="normal", text_color="gray"), "below")

        return maing

    def _prepare_average_source_data(self, average):
        """Prepare averages as a dict to be used as a ColumnDataSource."""
        source = {}

        source['x_axis'] = list(average)

        for decade in average.keys():
            for gln in average[decade].keys():
                if gln not in source:
                    source[gln] = []

                mean = average[decade][gln]['average']
                if math.isnan(mean):
                    mean = '-'

                source[gln].append(mean)

        # We add a new decade with nan values to show the last decade mean values
        source['x_axis'].append(source['x_axis'][-1] + 10)

        keys = list(source)
        keys.remove('x_axis')

        for gln in keys:
            source[gln].append(math.nan)

        return source, keys

    def _meang_get_tooltips_renderer(self, meang, average):
        """Get the render which will display the tooltips."""
        renderers = []

        # We render tooltips only in one line, use that with maximum valid values
        line_name = Average.get_average_tooltips_line_name(average)

        for render in meang.renderers:
            if render.glyph.y == line_name:
                renderers.append(render)
                break

        return renderers

    def _meang_configure_tooltips(self, legend, source_keys):
        """Configure the tooltips to be shown."""
        tooltips = []

        tooltips.append(("Década", "@x_axis"))

        for ind, y_name in enumerate(source_keys):
            format_y = f"@{y_name}"
            format_y += '{0.00} ºC'
            legend_name = legend[ind].capitalize()

            tooltips.append((f"{legend_name}", format_y))

        return tooltips

    def _configure_mean_graph(self, average, legend):
        """Create the average per decade per measurement graph.

        :param average: Dictionary containing the average per decade
        :type average: dict
        """
        title = 'Media de las temperaturas máximas, mínimas y medias por década'

        meang = figure(tools="xpan", toolbar_location=None, name="meang", width_policy="max",
                       background_fill_color="#efefef", title=title, margin=(0, 10, 0, 0), y_axis_type=None)

        # Prepare source data
        source, source_keys = self._prepare_average_source_data(average)

        source_data = ColumnDataSource(source)

        # Plot lines and scatters
        for ind, y_name in enumerate(source_keys):
            meang.line('x_axis', y_name, line_color=self.graph_lines_colors[ind], source=source_data)
            meang.scatter('x_axis', y_name, fill_color=self.graph_lines_colors[ind], size=8, source=source_data)

        # Configure HoverTool
        # Use only one line to render the tooltips
        renderers = self._meang_get_tooltips_renderer(meang, average)

        tooltips = self._meang_configure_tooltips(legend, source_keys)

        meang.add_tools(HoverTool(tooltips=tooltips, renderers=renderers, mode="vline", attachment="above", line_policy='prev'))

        # Configure Crosshair tool
        width = Span(dimension="width", line_width=1)
        height = Span(dimension="height", line_width=1)
        meang.add_tools(CrosshairTool(overlay=[width, height]))

        # Set the y axis tickers and labels
        ticker = SingleIntervalTicker(interval=1, num_minor_ticks=5)
        yaxis = LinearAxis(ticker=ticker)
        meang.add_layout(yaxis, 'left')

        meang.yaxis.axis_label = 'Temperatura ºC'
        meang.xaxis.axis_label = 'Décadas'

        # Set the x axis labels
        meang.xaxis.ticker = source['x_axis']

        # Plot horizontal lines in grid
        meang.add_layout(Grid(dimension=1, ticker=yaxis.ticker))
        meang.ygrid.grid_line_alpha = 0.4
        meang.ygrid.grid_line_color = 'gray'
        meang.grid.visible = True

        return meang

    def _render_template(self, maing, meang, html_file_name, title):
        """Write the html file contents.

        :param maing: Bokeh figure to represent the main graph
        :type maing: Figure
        :param meang: Bokeh figure to represent the mean graph
        :type meang: Figure
        :param html_file_name: the path to the static html file to be generated
        :type html_file_name: Path
        """
        template = """
        {% block contents %}
        <div class="row">
        <div class="col-sm-12">
        {{ embed(roots.maing) }}
        </div>
        </div>
        <div class="row" style="display: flex; justify-content: center">
        <div class="col-sm-12" style="flex: 0 1 50%;">
        {{ embed(roots.meang) }}
        </div>
        </div>
        {% endblock %}"""

        curdoc().add_root(maing)
        curdoc().add_root(meang)

        html = file_html(models=[maing, meang], template=template, resources=CDN, title=title)

        with open(html_file_name, 'w') as f:
            f.write(html)

    def _build_bokeh_plots(self, html_file_name, station_data, data_dict, legend, average):
        """Configure the Bokeh Plots.

        :param html_file_name: the path to the static html file to be generated
        :type html_file_name: Path
        :param station_data: station data to be written to the html file
        :type station_data: dict
        :param data_dict: data to be plotted into the html file as Bokeh figures.
        :type data_dict: dict
        :param legend: information to be placed into the Bokeh Legend
        :type legend: dict
        :param average: data to be plotted into the Bokeh meang figure
        :type average: dict
        """
        # Get a list of the data_dict keys
        dict_keys = list(data_dict)
        dict_keys.remove('x_axis')

        data_staid = station_data[0]
        station_name = station_data[2]

        # Register the file path and the html title
        title = f'Estación: {data_staid} - {station_name}'
        # output_file(html_file_name, title=title)

        # Instantiate a ColumnDataSource with the data
        bok_data = ColumnDataSource(data_dict)

        # Generate plots
        maing = self._configure_main_graph(dict_keys, station_data, bok_data, legend)

        mean = self._configure_mean_graph(average, legend)

        self._render_template(maing, mean, html_file_name, title)

    def create_html_file(self, data_dict, legend, station_data, average, current_graph_dir, tmp_graph_dir):
        """Create the html file with the interactive graph.

        :param data_dict: Dictionary which contains the data for x and y axis.
        :type data_dict: dict
        :param legend: list with the texts for sources legend
        :param legend: list
        :param station_data: Dictionary with the station data.
        :type data_staid: dict
        :param average: Dictionary containing the average per decade
        :type average: dict
        :param current_graph_dir: directory where to place the resulting html file
        :type current_graph_dir: str
        :param tmp_graph_dir: directory where to place the temporary html file
        :type tmp_graph_dir: str
        """
        data_staid = station_data[0]

        # Create the html file path. If the file exists, then write it first into the tmp directory
        html_file_name = current_graph_dir / f'STA_{data_staid}.html'

        file_exists = html_file_name.exists()

        if file_exists:
            return
            html_file_name = tmp_graph_dir / f'STA_{data_staid}.html'

        self._build_bokeh_plots(html_file_name, station_data, data_dict, legend, average)

        # If html file existed then move it from tmp to current directory
        if file_exists and html_file_name.exists():
            html_file_name.replace(current_graph_dir / f'STA_{data_staid}.html')
