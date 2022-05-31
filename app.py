import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from urllib.request import urlopen
import json
from plotly.subplots import make_subplots
import time

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

def getTimeStamp(dt):
    return int(time.mktime(dt.timetuple()))

def getDateTime(unix):
    return pd.to_datetime(unix, unit = 's').strftime('%Y-%m-%d')

def getMarks(start, end, Nth=30):

    result = {}
    for i, date in enumerate(pd.date_range(start,end)):
        if(i%Nth == 1):
            result[getTimeStamp(date)] = str(date.strftime('%Y-%m-%d'))

    return result

jurisdiction = pd.read_csv("COVID-19_Vaccinations_in_the_United_States_Jurisdiction.csv")
jurisdiction['Date'] = pd.to_datetime(jurisdiction['Date'])

county = pd.read_csv("COVID-19_Vaccinations_in_the_United_States_County.csv")
county['Date'] = pd.to_datetime(county['Date'])
county['FIPS'] = county['FIPS'].astype(str)

transmission = pd.read_csv("United_States_COVID-19_County_Level_of_Community_Transmission_as_Originally_Posted.csv")
transmission['report_date'] = pd.to_datetime(transmission['report_date'])
transmission['fips_code'] = transmission['fips_code'].astype(str)
transmission['cases_per_100K_7_day_count_change'] = transmission['cases_per_100K_7_day_count_change'].str.replace(",", "")
transmission['cases_per_100K_7_day_count_change'] = pd.to_numeric(transmission['cases_per_100K_7_day_count_change'], errors= 'coerce')

state_list = {
'AK': 'Alaska',
'AL': 'Alabama',
'AR': 'Arkansas',
'AZ': 'Arizona',
'CA': 'California',
'CO': 'Colorado',
'CT': 'Connecticut',
'DE': 'Delaware',
'FL': 'Florida',
'GA': 'Georgia',
'HI': 'Hawaii',
'IA': 'Iowa',
'ID': 'Idaho',
'IL': 'Illinois',
'IN': 'Indiana',
'KS': 'Kansas',
'KY': 'Kentucky',
'LA': 'Louisiana',
'MA': 'Massachusetts',
'MD': 'Maryland',
'ME': 'Maine',
'MI': 'Michigan',
'MN': 'Minnesota',
'MO': 'Missouri',
'MS': 'Mississippi',
'MT': 'Montana',
'NC': 'North Carolina',
'ND': 'North Dakota',
'NE': 'Nebraska',
'NH': 'New Hampshire',
'NJ': 'New Jersey',
'NM': 'New Mexico',
'NV': 'Nevada',
'NY': 'New York',
'OH': 'Ohio',
'OK': 'Oklahoma',
'OR': 'Oregon',
'PA': 'Pennsylvania',
'RI': 'Rhode Island',
'SC': 'South Carolina',
'SD': 'South Dakota',
'TN': 'Tennessee',
'TX': 'Texas',
'UT': 'Utah',
'VA': 'Virginia',
'VT': 'Vermont',
'WA': 'Washington',
'WI': 'Wisconsin',
'WV': 'West Virginia',
'WY': 'Wyoming'
}

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.H1("US COVID-19 Data Tracker", style = {'text-align':'center'}),
        dcc.RadioItems(
            id = 'vaccine_status',
            options=[
                {'label': 'Fully Vaccinated', 'value': 'FV'},
                {'label': 'Atleast 1 dose', 'value': 'OD'},
            ],
            value='FV', 
            style = {'text-align':'center', 'font-size': '20px'}
        ),
        html.Br(),
        dcc.Graph(id = 'graph'),
        html.Br(),
        dcc.Slider(
            id = 'year',
            min = getTimeStamp(jurisdiction['Date'].min()),
            max = getTimeStamp(jurisdiction['Date'].max()),
            marks=getMarks(jurisdiction['Date'].min(),
                            jurisdiction['Date'].max()),
            value = getTimeStamp(jurisdiction['Date'].max())
        ),
        html.Br(),
        html.Div(id='slider-output-container', style = {'text-align':'center', 'font-size': '18px'}),
        html.Br(),
        html.Hr(),
        html.Br(),
        html.Br()
    ]),


    html.Div([
        html.Div([
            dcc.Dropdown(
                id = 'state',
                options = [{'label':state_list[i], 'value': i} for i in state_list.keys()],
                value = 'IL',
                clearable=False
            ),
            html.Br(),
            dcc.RadioItems(
                id = 'vaccine_status_state',
                options=[
                    {'label': 'Fully Vaccinated', 'value': 'FV'},
                    {'label': 'Atleast 1 dose', 'value': 'OD'},
                ],
                value='FV', 
                style = {'text-align':'center', 'font-size': '20px'}
            ),
            html.Br(),
            dcc.Graph(id = 'state_fig'),
            html.Br(),
            dcc.Slider(
                id = 'county_year'
            ),
            html.Br(),
            html.Div(id='county-slider-output-container', style = {'text-align':'center', 'font-size': '18px'})
        ], style={'padding': 10, 'flex': 1}),


        html.Div([
            dcc.Dropdown(
                id = 'county',
                clearable=False
            ),
            html.Br(),
            dcc.RangeSlider(
                id = 'rangeslider',
                allowCross=False
            ),
            html.Br(),
            html.Div(id = 'range-slider-ouput', style = {'text-align':'center', 'font-size': '18px'}),
            html.Br(),
            dcc.Graph(id="positivity")
        ], style={'padding': 10, 'flex': 1})
    ], style={'display': 'flex', 'flex-direction': 'row'})
])

# Top part

@app.callback(
    Output('slider-output-container', 'children'),
    Input('year', 'value')
)
def update_output(value):
    return 'You have selected "{}"'.format(getDateTime(value))

@app.callback(
    Output('graph','figure'),
    Input('vaccine_status', 'value'),
    Input('year', 'value')
)
def update_vaccine_pct(vaccine_status, date_value):
    str_vaccine = "Fully Vaccinated" if vaccine_status == 'FV' else "Atleast 1 dose"

    selected_data = jurisdiction[jurisdiction['Date'] == getDateTime(date_value)]
    col_name = 'Series_Complete_Pop_Pct' if vaccine_status == 'FV' else 'Administered_Dose1_Pop_Pct'
    
    plotting_data = selected_data[['Location', col_name]].reset_index(drop = True)
    
    fig = go.Figure(data=go.Choropleth(
        locations=plotting_data['Location'],
        z = plotting_data[col_name].astype(float), 
        zmin = 0,
        zmax = 100,
        locationmode = 'USA-states', 
        colorscale = 'Viridis',
        colorbar_title = str_vaccine + " Percentage",
        hovertext = plotting_data['Location'],
        hovertemplate = "State: %{hovertext} <br>" + "Percentage of " + str_vaccine + ": %{z}<extra></extra>"
    ))

    fig.update_layout(
        title_text = 'COVID-19 vaccine rates by state',
        geo_scope='usa',
    )

    return fig

# Bottom Left

@app.callback(
    Output('county_year', 'min'),
    Output('county_year', 'max'),
    Output('county_year', 'marks'),
    Input('state', 'value')
)
def update_state_slider(state):
    selected_data = county[county['Recip_State'] == state]

    return getTimeStamp(selected_data['Date'].min()), getTimeStamp(selected_data['Date'].max()), getMarks(selected_data['Date'].min(),selected_data['Date'].max(), Nth = 60)

@app.callback(
    Output('county_year', 'value'),
    Input('county_year', 'max')
)
def update_slider_value(slidermax):
    return slidermax

@app.callback(
    Output('county-slider-output-container', 'children'),
    Input('county_year', 'value')
)
def update_state_output(value):
    return 'You have selected "{}"'.format(getDateTime(value))

@app.callback(
    Output('state_fig','figure'),
    Input('state', 'value'),
    Input('vaccine_status_state', 'value'),
    Input('county_year', 'value')
)
def update_state_vaccine_pct(state, vaccine_status, date_value):
    str_vaccine = "Fully Vaccinated" if vaccine_status == 'FV' else "Atleast 1 dose"
    
    selected_data = county[(county['Recip_State'] == state) & (county['Date'] == getDateTime(date_value))]
    selected_data = selected_data[selected_data['FIPS'].notnull()]

    plotting_data = selected_data[selected_data['FIPS'] != 'UNK']

    col_name = 'Series_Complete_Pop_Pct' if vaccine_status == 'FV' else 'Administered_Dose1_Pop_Pct'

    fig = go.Figure(data=go.Choropleth(
        locations=plotting_data['FIPS'],
        z = plotting_data[col_name].astype(float), 
        zmin = 0,
        zmax = 100,
        geojson=counties,
        colorscale = 'Viridis',
        colorbar_title = str_vaccine + " Percentage",
        hovertext = plotting_data['Recip_County'],
        hovertemplate = "County: %{hovertext} <br>" + "Percentage of " + str_vaccine + ": %{z}<extra></extra>"
    ))

    fig.update_layout(
        title_text = 'COVID-19 vaccine rates by counties'
    )

    if state == "AK":
        fig.update_geos(
            lonaxis_range=[20, 380],
            projection_scale=6,
            center=dict(lat=61),
            visible=False)
    else:
        fig.update_geos(fitbounds="locations", visible=True, scope='usa')

    return fig

# Bottom Right

@app.callback(
    Output('county', 'options'),
    Output('county', 'value'),
    Input('state', 'value')
)
def update_county_dropdown(state):
    county_list = sorted(transmission[transmission['state_name'] == state_list[state]]['county_name'].unique())
    return [{'label':i, 'value': i} for i in county_list], county_list[0]

@app.callback(
    Output('rangeslider', 'min'),
    Output('rangeslider', 'max'),
    Output('rangeslider', 'marks'),
    Input('state', 'value'),
    Input('county', 'value')
)
def update_range_slider(state, county_name):
    selected_data = transmission[(transmission['state_name'] == state_list[state]) & (transmission['county_name'] == county_name)]

    return getTimeStamp(selected_data['report_date'].min()), getTimeStamp(selected_data['report_date'].max()), getMarks(selected_data['report_date'].min(),selected_data['report_date'].max(), Nth = 15)

@app.callback(
    Output('rangeslider', 'value'),
    Input('rangeslider', 'min'),
    Input('rangeslider', 'max')
)
def update_slider_value(slidermin, slidermax):
    return [slidermin, slidermax]

@app.callback(
    Output('range-slider-ouput', 'children'),
    Input('rangeslider', 'value')
)
def update_range_slider_output(value):
    return 'You have selected "{}" to "{}"'.format(getDateTime(value[0]), getDateTime(value[1]))

@app.callback(
    Output('positivity', 'figure'),
    Input('rangeslider', 'value'),
    Input('state', 'value'),
    Input('county', 'value')
)
def update_positivity(date, state_name, county_name):
    selected_data = transmission[(transmission['state_name'] == state_list[state_name]) & (transmission['county_name'] == county_name)]

    plotting_data = selected_data[(selected_data['report_date'] >= getDateTime(date[0])) & 
    (selected_data['report_date'] <= getDateTime(date[1]))].sort_values(by = 'report_date')

    fig = make_subplots(rows=2, cols=1, subplot_titles=("Daily % Positivity - 7 day Moving Average", "Daily New Cases per 100k - 7 day Moving Average"))
    fig.append_trace(go.Scatter(x=plotting_data['report_date'], y=plotting_data['percent_test_results_reported_positive_last_7_days'], 
        hovertemplate = "Date: %{x} <br>" + "7 day Moving Average of Positivity % : %{y}<extra></extra>"),
                  row=1, col=1)

    fig.append_trace(go.Scatter(x=plotting_data['report_date'], y=plotting_data['cases_per_100K_7_day_count_change'],
        hovertemplate = "Date: %{x} <br>" + "7 day Moving Average of New Cases per 100k : %{y}<extra></extra>"),
                  row=2, col=1)

    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)

    fig.update_yaxes(title_text="% Positivity", row=1, col=1)
    fig.update_yaxes(title_text="New Cases per 100k", row=2, col=1)

    fig.update_layout(height=500, width=700, showlegend = False,
                      title_text="7 day Moving Average Time Series")
    return fig

if __name__ == '__main__':
    app.run_server(debug = False)
