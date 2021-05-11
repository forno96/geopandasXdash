# resurces
# https://github.com/italia/covid19-opendata-vaccini
# https://github.com/openpolis/geojson-italy

# load libs
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go
import plotly.express as px
import geopandas as gpd
import pandas as pd
from numerize.numerize import numerize
import dash, sys, json, requests

# load geojson
italy_regions_url = "https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_regions.geojson"
italy_regions = requests.get(italy_regions_url).json()
for region in italy_regions['features']:
    region["properties"]['codice_regione_ISTAT'] = region["properties"]['reg_istat_code_num']
italy_regions = gpd.GeoDataFrame.from_features(italy_regions["features"])

# load data
vaccine_data_url = "https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/somministrazioni-vaccini-summary-latest.csv"
df = pd.read_csv(vaccine_data_url)
lasDate = df['data_somministrazione'].max()
df = df.groupby(['codice_regione_ISTAT', 'nome_area'], as_index=False)[['totale', 'sesso_maschile', 'sesso_femminile', 'prima_dose', 'seconda_dose', 'categoria_operatori_sanitari_sociosanitari', 'categoria_personale_non_sanitario', 'categoria_ospiti_rsa', 'categoria_personale_scolastico', 'categoria_60_69', 'categoria_70_79', 'categoria_over80', 'categoria_soggetti_fragili', 'categoria_forze_armate', 'categoria_altro']].agg('sum')

# get italian population
pi = pd.read_csv("italian_population.csv")
pi = pi[pi['sesso'].values=='totale']
pi.drop('sesso', axis='columns', inplace=True)

# mix the 3
df = df.merge(pi, on="codice_regione_ISTAT")
geo_df = italy_regions.merge(df, on="codice_regione_ISTAT").set_index("reg_name")

# generate density
geo_df["area"] = round(geo_df.area * 10000, 0)
geo_df["densita"] = round(geo_df.totale_abitanti/geo_df["area"], 0)
geo_df["perc_vac"] = round((100*geo_df["totale"])/geo_df["totale_abitanti"], 2)

external_stylesheets = [
    { 'href': 'https://cdn.jsdelivr.net/npm/bulma@0.9.2/css/bulma-rtl.min.css',                     'rel': 'stylesheet' },
    { 'href': 'https://cdn.jsdelivr.net/npm/bulma-divider@0.2.0/dist/css/bulma-divider.min.css',    'rel': 'stylesheet' },
    { 'href': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css',         'rel': 'stylesheet' },
    { 'href': 'static/custom.css',                                                                  'rel': 'stylesheet' }
]

app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets
)
app.title = "GeoPandas x Dash"

field2show = [
    {'label': 'Totale', 'value': "totale"},
    {'label': 'Prima Dose', 'value': "prima_dose"},
    {'label': 'Seconda Dose', 'value': "seconda_dose"},
    {'label': 'Sesso Maschile', 'value': "sesso_maschile"},
    {'label': 'Sesso Femminile', 'value': "sesso_femminile"},
    {'label': 'Categoria Operatori Sanitari', 'value': "categoria_operatori_sanitari_sociosanitari"},
    {'label': 'Categoria Personale non Sanitario', 'value': "categoria_personale_non_sanitario"},
    {'label': 'Categoria Ospiti RSA', 'value': "categoria_ospiti_rsa"},
    {'label': 'Categoria Personale Scolastico', 'value': "categoria_personale_scolastico"},
    {'label': 'Categoria 60/69', 'value': "categoria_60_69"},
    {'label': 'Categoria 70/79', 'value': "categoria_70_79"},
    {'label': 'Categoria Over 80', 'value': "categoria_over80"},
    {'label': 'Categoria Soggetti Fragili', 'value': "categoria_soggetti_fragili"},
    {'label': 'Categoria Forze Armate', 'value': "categoria_forze_armate"},
    {'label': 'Categoria Altro', 'value': "categoria_altro"}
]

app.layout = html.Div([
    html.Div([], className="is-hidden", id="hidden"),
    html.Div([
        html.Div([
            html.H1([
                html.A(["Geopandas"], className="has-text-primary", href="https://geopandas.org/index.html", target="_blank"),
                " X ",
                html.A(["Dash"], className="has-text-info", href="https://dash.plotly.com/introduction", target="_blank")
            ], id="title", className="title is-1 has-text-centered"),
            html.Div([
                html.Div([
                    html.Div([
                        html.Div([
                            html.P(["Selectors"], className="is-size-4 mb-4"),
                            html.P(["Field for Map1"], className="is-size-6 has-text-grey-light has-text-left"),
                            dcc.Dropdown(
                                id = 'field2showMap1', clearable=False,
                                options = field2show,
                                value = field2show[0]['value']
                            ),

                            html.Br(),
                            html.P(["Field for Map2"], className="is-size-6 has-text-grey-light has-text-left"),
                            dcc.Dropdown(
                                id = 'field2showMap2', clearable=False,
                                options = field2show,
                                value = field2show[1]['value']
                            ),

                            html.Br(),
                            html.P(["Max Km square"], className="is-size-6 has-text-grey-light has-text-left"),
                            dcc.Slider(id = "max_square_km"),

                            html.Br(),
                            html.P(["Max Density"], className="is-size-6 has-text-grey-light has-text-left"),
                            dcc.Slider(id = "max_density")
                        ])
                    ], className="column is-3", style={"position": "relative"}),
                    html.Div(className="is-divider-vertical px-3"),
                    html.Div([
                        html.P(["Map 1"], className="is-size-4"),
                        dcc.Loading(
                            type="circle",
                            children=html.Div([dcc.Graph(id="map1")], style={"minHeight":"300px"})
                        )
                    ], className="column"),
                    html.Div(className="is-divider-vertical px-3"),
                    html.Div([
                        html.P(["Map 2"], className="is-size-4"),
                        dcc.Loading(
                            type="circle",
                            children=html.Div([dcc.Graph(id="map2")], style={"minHeight":"300px"})
                        )
                    ], className="column")
                ], className="columns is-gapless"),
                html.Div(className="is-divider my-3"),
                html.Div([
                    html.Div([
                        html.P([_[0]], className="is-size-7 has-text-grey-light"),
                        html.P([_[1]], className="is-size-4 has-text-info has-text-weight-bold", id=_[2])
                    ], className="column")
                    for _ in [
                        ("Max Km Square",0, "display_max_square_km"),
                        ("Max Density of Abitants/Km Square", 0, "display_max_density"),
                        ("Total vaccinated", numerize(int(geo_df["totale"].sum())), ""),
                        ("Percent Vacinnated", f'{round((100*int(geo_df["totale"].sum()))/int(geo_df["totale_abitanti"].sum()), 2)}%', ""),
                        ("Last update", lasDate, "")
                    ]
                ], className="columns")
            ], className="box"),
            dcc.Markdown('''
                Example of code
                ```py
                import pandas as pd
                import geopandas as gpd

                vaccine_data_url = "https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/somministrazioni-vaccini-summary-latest.csv"
                italy_regions_url = "https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_regions.geojson"

                df = pd.read_csv(vaccine_data_url)
                df = df.groupby(['codice_regione_ISTAT'], as_index=False)[['totale', 'sesso_maschile', 'sesso_femminile']].agg('sum')

                italy_regions = requests.get(italy_regions_url).json()
                for region in italy_regions['features']:
                    region["properties"]['codice_regione_ISTAT'] = region["properties"]['reg_istat_code_num']
                italy_regions = gpd.GeoDataFrame.from_features(italy_regions["features"])

                geo_df = italy_regions.merge(df, on="codice_regione_ISTAT").set_index("reg_name")
                geo_df.plot("totale")
                ```
            ''', className="has-text-left")
        ], className="container has-text-centered maxWidth")
    ], className="hero-body")
], className="hero is-light is-fullheight")


@app.callback(
    Output('max_square_km', 'marks'),
    Output('max_square_km', 'min'),
    Output('max_square_km', 'max'),
    Output('max_square_km', 'value'),
    Input('hidden', 'children')
)
def loadMaxSquareKM(hidden):
    return loadSlider("area", "km^2")

@app.callback(
    Output('max_density', 'marks'),
    Output('max_density', 'min'),
    Output('max_density', 'max'),
    Output('max_density', 'value'),
    Input('hidden', 'children')
)
def loadMaxSquareKM(hidden):
    return loadSlider("densita", "ab/km^2")

@app.callback(
    Output('display_max_square_km', 'children'),
    Input('max_square_km', 'value'),
    prevent_initial_call=True
)
def diplayOnGauge(maxSquareKm):
    return numerize(maxSquareKm)

@app.callback(
    Output('display_max_density', 'children'),
    Input('max_density', 'value'),
    prevent_initial_call=True
)
def diplayOnGauge(maxDensity):
    return numerize(maxDensity)

@app.callback(
    Output('map1', 'figure'),
    Input('field2showMap1', 'value'),
    Input('max_square_km', 'value'),
    Input('max_density', 'value'),
    prevent_initial_call=True
)
def displayMap1(field, maxSquareKm, maxDensity):
    return diplayMap(field, maxSquareKm, maxDensity)
@app.callback(
    Output('map2', 'figure'),
    Input('field2showMap2', 'value'),
    Input('max_square_km', 'value'),
    Input('max_density', 'value'),
    prevent_initial_call=True
)
def displayMap2(field, maxSquareKm, maxDensity):
    return diplayMap(field, maxSquareKm, maxDensity)

#/km^2
def loadSlider(field, measure):
    max = int(geo_df[field].max())
    min = int(geo_df[field].min())
    marks={
        min: f"{numerize(min)} {measure}",
        max: f"{numerize(max)} {measure}"
    }
    value=max
    return marks, min, max, value

def diplayMap(field, maxSquareKm, maxDensity):
    hover_data = list(set(['area', 'totale', 'densita', 'perc_vac', field]))

    mask = (geo_df['area'] <= maxSquareKm) & (geo_df['densita'] <= maxDensity)
    tmp = geo_df.loc[mask]

    fig = px.choropleth_mapbox(
        tmp,
        geojson=tmp.geometry,
        locations=tmp.index,
        hover_data=hover_data,
        color=field,
        color_continuous_scale=px.colors.sequential.GnBu,
        opacity=0.5,
        center={"lat": 41.8719, "lon": 12.5694}, zoom=4,
        mapbox_style="carto-positron",
        labels={'area':'Area', 'densita':'Densità', 'perc_vac': 'Percentuale vaccinati','reg_name': 'Nome regione', 'totale': 'Totale', 'prima_dose': 'Prima dose', 'seconda_dose': 'Seconda dose', 'sesso_maschile': 'Sesso maschile', 'sesso_femminile': 'Sesso femminile', 'categoria_operatori_sanitari_sociosanitari': 'Operatori sanitari', 'categoria_personale_non_sanitario': 'Personale non sanitario', 'categoria_ospiti_rsa': 'Ospiti rsa', 'categoria_personale_scolastico': 'Personale scolastico', 'categoria_60_69': '60/69', 'categoria_over80': 'Over 80', 'categoria_soggetti_fragili': 'Soggetti fragili', 'categoria_forze_armate': 'Forze armate', 'categoria_altro': 'Altro'}
    )
    fig.update_layout(margin=dict(b=0,t=40,l=0,r=0))

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
