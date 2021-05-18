# resurces
# https://github.com/italia/covid19-opendata-vaccini
# https://github.com/openpolis/geojson-italy

# load libs
from dash.dependencies import Input, Output, State
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

# get italian population and mix on df
pi = pd.read_csv("italian_population.csv")
for type in ['totale', 'maschi', 'femmine']:
    tmp = pi.loc[pi['sesso'].values==type].copy()
    tmp.drop('sesso', axis='columns', inplace=True)
    tmp = tmp.rename(columns={"totale_abitanti": f"{type}_abitanti"})
    df = df.merge(tmp, on="codice_regione_ISTAT")

# mix the map
geo_df = italy_regions.merge(df, on="codice_regione_ISTAT").set_index("reg_name")

# generate density
geo_df["area"] = round(geo_df.area * 10000, 0)
geo_df["densita"] = round(geo_df.totale_abitanti/geo_df["area"], 0)
for field, populationfield in [('totale', 'totale'), ('sesso_maschile', 'maschi'), ('sesso_femminile', 'femmine')]:#, 'prima_dose', 'seconda_dose', 'sesso_maschile', 'sesso_femminile', 'categoria_operatori_sanitari_sociosanitari', 'categoria_personale_non_sanitario', 'categoria_ospiti_rsa', 'categoria_personale_scolastico', 'categoria_60_69', 'categoria_70_79', 'categoria_over80', 'categoria_soggetti_fragili', 'categoria_forze_armate', 'categoria_altro']:
    geo_df[f"perc_vac_{field}"] = round((100*geo_df[field])/geo_df[f"{populationfield}_abitanti"], 2)

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
    {'label': 'Percentuale Vaccinati Totale', 'value': 'perc_vac_totale'},
    {'label': 'Sesso Maschile', 'value': "sesso_maschile"},
    {'label': 'Percentuale Vaccinati Maschi', 'value': 'perc_vac_sesso_maschile'},
    {'label': 'Sesso Femminile', 'value': "sesso_femminile"},
    {'label': 'Percentuale Vaccinati Femmine', 'value': 'perc_vac_sesso_femminile'},
    {'label': 'Prima Dose', 'value': "prima_dose"},
    {'label': 'Seconda Dose', 'value': "seconda_dose"},
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
                            html.P([html.Span([html.I([], className="fas fa-clipboard-list")], className="icon has-text-info"), " Selectors"], className="is-size-4 mb-4"),
                            html.P([html.Span([html.I([], className="fas fa-map")], className="icon has-text-primary"), " Field for Map 1"], className="is-size-6 has-text-grey-light has-text-left"),
                            dcc.Dropdown(
                                id = 'field2showMap1', clearable=False,
                                options = field2show,
                                value = field2show[0]['value']
                            ),

                            html.Br(),
                            html.P([html.Span([html.I([], className="fas fa-map")], className="icon has-text-primary-dark"), " Field for Map 2"], className="is-size-6 has-text-grey-light has-text-left"),
                            dcc.Dropdown(
                                id = 'field2showMap2', clearable=False,
                                options = field2show,
                                value = field2show[1]['value']
                            ),

                            html.Br(),
                            html.P([html.Span([html.I([], className="fas fa-ruler")], className="icon"), " Max Km square"], className="is-size-6 has-text-grey-light has-text-left"),
                            dcc.RangeSlider(id = "range_square_km"),

                            html.Br(),
                            html.P([html.Span([html.I([], className="fas fa-users")], className="icon"), " Max Density"], className="is-size-6 has-text-grey-light has-text-left"),
                            dcc.RangeSlider(id = "range_density")
                        ])
                    ], className="column is-3", style={"position": "relative"}),
                    html.Div(className="is-divider-vertical px-3"),
                    html.Div([
                        html.P([html.Span([html.I([], className="fas fa-map")], className="icon has-text-primary"), " Map 1"], className="is-size-4"),
                        dcc.Loading(
                            type="circle",
                            children=html.Div([dcc.Graph(id="map1")], style={"minHeight":"300px"})
                        )
                    ], className="column"),
                    html.Div(className="is-divider-vertical px-3"),
                    html.Div([
                        html.P([html.Span([html.I([], className="fas fa-map")], className="icon has-text-primary-dark"), "  Map 2"], className="is-size-4"),
                        dcc.Loading(
                            type="circle",
                            children=html.Div([dcc.Graph(id="map2")], style={"minHeight":"300px"})
                        )
                    ], className="column")
                ], className="columns is-gapless"),
                html.Div(className="is-divider my-3"),
                html.Div([
                    html.Div([
                        html.P([html.Span([html.I([], className=icon)], className="icon"), f" ", label], className="is-size-7 has-text-grey-light"),
                        html.P([value], className="is-size-4 has-text-info has-text-weight-bold", id=id)
                    ], className="column")
                    for label, value, id, icon in [
                        (u"Max Km\u00B2", 0, "display_min_square_km", "fas fa-ruler"),
                        (u"Max Km\u00B2", 0, "display_max_square_km", "fas fa-ruler"),
                        (u"Min Ab/Km\u00B2", 0, "display_min_density", "fas fa-users"),
                        (u"Max Ab/Km\u00B2", 0, "display_max_density", "fas fa-users"),
                        ("Total vaccinated", numerize(int(geo_df["totale"].sum())), "", "fas fa-syringe"),
                        ("Percent Vacinnated", f'{round((100*int(geo_df["totale"].sum()))/int(geo_df["totale_abitanti"].sum()), 2)}%', "", "fas fa-percentage"),
                        ("Last update", lasDate, "", "far fa-calendar-alt")
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
    ], className="hero-body"),
    html.Footer([
        html.Div([
            html.A([html.Span([html.I([], className=_[2])], className="icon"), f" {_[0]}"], href=_[1], className="column")
            for _ in [
                ("Css by Bulma", "https://bulma.io", "fab fa-css3-alt has-text-primary"),
                ("Icons by FontAwesome", "https://fontawesome.com/", "fab fa-font-awesome has-text-info"),
                ("Vaccine data", "https://github.com/italia/covid19-opendata-vaccini", "fas fa-syringe has-text-success"),
                ("Italy map", "https://github.com/openpolis/geojson-italy", "fas fa-map has-text-warning"),
                ("People data", "http://dati.istat.it/Index.aspx?DataSetCode=DCIS_POPRES1", "fas fa-users has-text-danger")
            ]
        ], className="content has-text-centered columns is-centered")
    ], className="footer")
], className="hero is-light is-fullheight")


@app.callback(
    Output('range_square_km', 'marks'),
    Output('range_square_km', 'min'),
    Output('range_square_km', 'max'),
    Output('range_square_km', 'value'),
    Input('hidden', 'children')
)
def loadRangeSquareKM(hidden):
    return loadSlider("area", u"Km\u00B2")
@app.callback(
    Output('range_density', 'marks'),
    Output('range_density', 'min'),
    Output('range_density', 'max'),
    Output('range_density', 'value'),
    Input('hidden', 'children')
)
def loadRangeDensity(hidden):
    return loadSlider("densita", u"Ab/Km\u00B2")

@app.callback(
    Output('display_min_square_km', 'children'),
    Output('display_max_square_km', 'children'),
    Input('range_square_km', 'value'),
    prevent_initial_call=True
)
def diplayOnGauge(maxSquareKm):
    return numerize(maxSquareKm[0]), numerize(maxSquareKm[1])
@app.callback(
    Output('display_min_density', 'children'),
    Output('display_max_density', 'children'),
    Input('range_density', 'value'),
    prevent_initial_call=True
)
def diplayOnGauge(maxDensity):
    return numerize(maxDensity[0]), numerize(maxDensity[1])

@app.callback(
    Output('map1', 'figure'),
    Input('field2showMap1', 'value'),
    Input('range_square_km', 'value'),
    Input('range_density', 'value'),
    State('field2showMap2', 'value'),
    prevent_initial_call=True
)
def displayMap1(field, maxSquareKm, maxDensity, compareField):
    return diplayMap(field, maxSquareKm[0], maxSquareKm[1], maxDensity[0], maxDensity[1], compareField)
@app.callback(
    Output('map2', 'figure'),
    Input('field2showMap2', 'value'),
    Input('range_square_km', 'value'),
    Input('range_density', 'value'),
    State('field2showMap1', 'value'),
    prevent_initial_call=True
)
def displayMap2(field, maxSquareKm, maxDensity, compareField):
    return diplayMap(field, maxSquareKm[0], maxSquareKm[1], maxDensity[0], maxDensity[1], compareField)

#/km^2
def loadSlider(field, measure):
    max = int(geo_df[field].max())
    min = int(geo_df[field].min())
    marks={
        min: f"{numerize(min)} {measure}",
        max: f"{numerize(max)} {measure}"
    }
    value=[min, max]
    return marks, min, max, value

def diplayMap(field, minSquareKm, maxSquareKm, minDensity, maxDensity, compareField):
    hover_data = list(set(['area', 'totale', 'densita', 'perc_vac_totale', field, compareField]))

    mask = (minSquareKm <= geo_df['area']) & (geo_df['area'] <= maxSquareKm) & (minDensity <= geo_df['densita']) & (geo_df['densita'] <= maxDensity)
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
        labels={'area':'Area', 'densita':'Densità', 'perc_vac_totale': 'Percentuale vaccinati', 'perc_vac_sesso_maschile': 'Percentuale vac. maschi', 'perc_vac_sesso_femminile': 'Percentuale vac. femmine','reg_name': 'Regione', 'totale': 'Totale', 'prima_dose': 'Prima dose', 'seconda_dose': 'Seconda dose', 'sesso_maschile': 'Sesso maschile', 'sesso_femminile': 'Sesso femminile', 'categoria_operatori_sanitari_sociosanitari': 'Operatori sanitari', 'categoria_personale_non_sanitario': 'Personale non sanitario', 'categoria_ospiti_rsa': 'Ospiti rsa', 'categoria_personale_scolastico': 'Personale scolastico', 'categoria_60_69': '60/69', 'categoria_over80': 'Over 80', 'categoria_soggetti_fragili': 'Soggetti fragili', 'categoria_forze_armate': 'Forze armate', 'categoria_altro': 'Altro'}
    )
    fig.update_layout(margin=dict(b=0,t=40,l=0,r=0))

    return fig

if __name__ == '__main__':
    app.run_server(host="0.0.0.0", debug=True)
