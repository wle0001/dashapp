import dash
import pandas as pd
import plotly.express as px
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from datetime import datetime as dt
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from datetime import date, timedelta
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
mapbox_access_token = 'pk.eyJ1IjoibGVmdHk2NjYiLCJhIjoiY2tyMmUwbTd3MmFicDJ0bDM4MWduNzM3ZiJ9.pDLUOLA--9M4NpkVOKWkzQ'

# -------------------- THE SET-UP ------------------------------------------------------

# ---------- SCAN DATA -----------------------
scan_path = 'scripts/'
SCAN = pd.read_csv(scan_path + 'SCAN_AL_SMS_only.csv')
#print('SCAN')
#print(SCAN.shape)
#print(SCAN.columns)

scan = SCAN[['Date', 'station','SMS-2.0in', 'SMS-4.0in', 'SMS-8.0in', 'SMS-20.0in','SMS-40.0in']].copy()
scan['Date'] = pd.to_datetime(scan['Date'],format='%Y-%m-%d')
scan.columns = ['Date', 'station','5cm','10cm','20cm','50cm', '100cm']
scan['station_type'] = 'SCAN'
scan_stations = list(scan['station'].unique())
# ---------- CRN DATA ----------------------
CRN = pd.read_csv(scan_path + 'CRN_AL_all.csv')
CRN2 = CRN.replace(to_replace=-99.0, value=np.nan)
#print('CRN')
crn = CRN2[['site', 'LST_DATE',
           'SOIL_MOISTURE_5_DAILY','SOIL_MOISTURE_10_DAILY',
           'SOIL_MOISTURE_20_DAILY','SOIL_MOISTURE_50_DAILY',
           'SOIL_MOISTURE_100_DAILY']].copy()
crn.columns = ['station','Date','5cm','10cm','20cm','50cm', '100cm']
crn['station_type'] = 'CRN'
crn['Date'] = pd.to_datetime(crn['Date'],format='%Y-%m-%d')
#print(crn.shape)
#print(crn.columns)
crn_stations = list(crn['station'].unique())

# ----------- METADATA ---------
compare = pd.read_csv(scan_path + 'CRN_SCAN_soil_meta_mini.csv')
mid_lon = (compare['longitude'].max() + compare['longitude'].min())/2
#print(mid_lon) # -86.7
mid_lat = (compare['latitude'].max() + compare['latitude'].min())/2
#print(mid_lat) #32.7

# This doesn't work with map access token
#compare['color'] = compare['station_type'].apply(lambda x: 'blue' if 'SCAN' in x else 'crimson')
#compare['shape'] = compare['station_type'].apply(lambda x: 'circle' if 'SCAN' in x else 'triangle')

# --------- OTHER STUFF ----------------
# can refer to colors by number - see the line chart
colors = px.colors.qualitative.Plotly
#colors = ['rgb(174,89,89)']

#app = dash.Dash(__name__)
# [DC] comment out this line requiring external css. The css will need to
# [DC]        be installed locally.
#app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB])
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server

# --------- GETTING THE 7-DAY AVERAGES OVERALL TABLE ---------------------
# subset to get just needed columns then get min date for soil moisture data for each station
scan_real_min = scan.dropna(how='all', subset=['5cm', '10cm', '20cm', '50cm', '100cm'])
min_scan_dates = scan.groupby('station')['Date'].min().reset_index(name='min_date')

crn_real_min = crn.dropna(how='all', subset=['5cm', '10cm', '20cm', '50cm', '100cm'])
min_crn_dates = crn_real_min.groupby('station')['Date'].min().reset_index(name='min_date')

# put the scan and crn start dates together as one df: depth_start_dates
depth_start_dates = min_scan_dates.append(min_crn_dates)

# get list of all possible stations. Need this to make the master_df below:
stations = depth_start_dates['station'].values.tolist()

big_df = scan_real_min.append(crn_real_min)
#print(big_df.shape)

depth_start_dates.set_index('station', inplace=True)
#print(depth_start_dates.head())
end = big_df['Date'].max()

# Making a df where we have all 7-day rolling averages for each station
master_df = pd.DataFrame()
for stn in stations:
    df1 = big_df[big_df['station']==stn]
    # get list of all possible dates from earliest collection to latest
    start = depth_start_dates.loc[stn,'min_date']
    dates = list(pd.date_range(start, end))
    # start new df with DATES column
    df_dates = pd.DataFrame(dates, columns=['DATES'])
    df = pd.merge(df_dates, df1, left_on='DATES', right_on='Date', how='left')
    #print(df1.shape)
    #print(df.shape)

    # Get rolling 7-day averages (no center=True or .shift()) - Ask to be sure
    # need at least 4 values to get 7-day avg
    df['5cm_7d'] = df['5cm'].rolling(window=7,min_periods=4).mean()
    df['10cm_7d'] = df['10cm'].rolling(window=7, min_periods=4).mean()
    df['20cm_7d'] = df['20cm'].rolling(window=7, min_periods=4).mean()
    df['50cm_7d'] = df['50cm'].rolling(window=7, min_periods=4).mean()
    df['100cm_7d'] = df['100cm'].rolling(window=7, min_periods=4).mean()
    # Get surface and root-zone means
    df['surface_7d_mean'] = (df['5cm_7d'] + df['10cm_7d']) / 2
    df['root_7d_mean'] = (df['20cm_7d'] + df['50cm_7d'] + df['100cm_7d']) / 3

    master_df = master_df.append(df)


# --- For making the line graph -----
def filled_line_graph(avg_df, select_df, layer, station):
    # long-winded to change labels in legend vs hover.
    # min (line only - no legend)
    line = go.Figure()
    line.add_trace(go.Scatter(x=avg_df['Date'], y=round(avg_df['min'], 4),
                              mode='lines',
                              line=dict(width=0.7),
                              line_color='rgb(174,89,89)',
                              name='min',
                              showlegend=False))
    # min to 10%
    line.add_trace(go.Scatter(x=avg_df['Date'], y=round(avg_df['10%'], 4),
                              fill='tonexty',
                              mode='lines',
                              line=dict(width=0.7),
                              line_color='rgb(174,89,89)',
                              name='min - 10%',
                              hoverinfo='skip'))
    # 10% - 25%
    line.add_trace(go.Scatter(x=avg_df['Date'], y=round(avg_df['25%'],4),
                              fill='tonexty',
                              mode='lines',
                              line=dict(width=0.7),
                              line_color='rgb(255,200,108)',
                              name='10% - 25%',
                              hoverinfo='skip'))
    # 25% - 75%
    line.add_trace(go.Scatter(x=avg_df['Date'], y=round(avg_df['75%'],4),
                              fill='tonexty',
                              mode='lines',
                              line=dict(width=0.7),
                              line_color='rgb(97,255,113)',
                              name='25% - 75%',
                              hoverinfo='skip'))
    # 75% - 80%
    line.add_trace(go.Scatter(x=avg_df['Date'], y=round(avg_df['80%'],4),
                              fill='tonexty',
                              mode='lines',
                              line=dict(width=0.7),
                              line_color='rgb(124,223,214)',
                              name='75% - 80%',
                              hoverinfo='skip'))
    # 90% - max
    line.add_trace(go.Scatter(x=avg_df['Date'], y=round(avg_df['max'],4),
                              fill='tonexty',
                              mode='lines',
                              line=dict(width=0.7),
                              line_color='rgb(101,102,251)',
                              name='80% - max',
                              hoverinfo='skip'))

    # Order of the hover info.
    # 5% line
    line.add_trace(go.Scatter(x=avg_df['Date'], y=round(avg_df['5%'],4), mode='lines',
                              name='5%',
                              line=dict(width=1.0, color='grey', dash='dash')))
    # 95% line
    line.add_trace(go.Scatter(x=avg_df['Date'], y=round(avg_df['95%'],4), mode='lines',
                              name='95%',
                              line=dict(width=1.0, color='grey', dash='dash')))
    # current line
    if layer == 'surface':
        my_col = 'surface_7d_mean'
        title = 'surface: 5 & 10cm'
    else:
        my_col = 'root_7d_mean'
        title = 'root zone: 20, 50, & 100cm'
    line.add_trace(go.Scatter(x=select_df['Date'], y=round(select_df[my_col],4), mode='lines',
                              name='current',
                              line=dict(width=2.5, color='black')))
    # And now the lines for hover info only - not legend
    line.add_trace(go.Scatter(x=avg_df['Date'], y=round(avg_df['10%'], 4),
                              mode='lines',
                              line=dict(width=0.7),
                              line_color='rgb(174,89,89)',
                              name='10%',
                              showlegend=False))
    line.add_trace(go.Scatter(x=avg_df['Date'], y=round(avg_df['25%'], 4),
                              mode='lines',
                              line=dict(width=0.7),
                              line_color='rgb(255,200,108)',
                              name='25%',
                              showlegend=False))
    line.add_trace(go.Scatter(x=avg_df['Date'], y=round(avg_df['75%'], 4),
                              mode='lines',
                              line=dict(width=0.7),
                              line_color='rgb(97,255,113)',
                              name='75%',
                              showlegend=False))
    line.add_trace(go.Scatter(x=avg_df['Date'], y=round(avg_df['80%'], 4),
                              mode='lines',
                              line=dict(width=0.7),
                              line_color='rgb(124,223,214)',
                              name='80%',
                              showlegend=False))
    line.add_trace(go.Scatter(x=avg_df['Date'], y=round(avg_df['max'], 4),
                              mode='lines',
                              line=dict(width=0.7),
                              line_color='rgb(101,102,251)',
                              name='max',
                              showlegend=False))
    # grid background as white
    text = '<span style="font-size: 20px;"><b>' + title + '<b>' + "<br><br>" + '<span style="font-size: 15px;"><b>' + station + '<b>'
    line.update_layout(title=dict(text=text,
                                  x=0.5, font=dict(family="Arial", size=20, color='black')),
                       plot_bgcolor="white",
                       xaxis=dict(showgrid=True, linecolor='black', gridcolor='rgb(240,240,240)', gridwidth=0.05),
                       yaxis=dict(showgrid=True, linecolor='black', gridcolor='rgb(240,240,240)', gridwidth=0.05),
                       hovermode='x')
    return line
# ----------------------

# --------------------- LAYOUT SECTION ---------------------------------------------------
# App Layout
app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1('Alabama Soil Moisture Network: AL-SoilNet',
                              className= 'text-center text-primary mb-4'), width=12)),
    dbc.Row(dbc.Col(html.Div(id='output_s'))),
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(id='station_type',
                         options=[
                             {'label': 'All', 'value': 'All Stations'},
                             {'label': 'SCAN', 'value': 'SCAN'},
                             {'label': 'CRN', 'value': 'CRN'},
                             {'label': 'Test Probe', 'value': 'Test Probe'}],
                         value='All Stations',
                         multi=False,
                         searchable=True,
                         placeholder='Select station type...',
                         style={'width':'60%'}
                         ),
            dcc.Graph(id="AL_map", config={'displayModeBar': True, 'showTips': True, 'doubleClick': False})
        ], style={'width': "50%"}),
        dbc.Col([
            dcc.DatePickerRange(id='my_date_picker_range',
                                calendar_orientation='horizontal',
                                day_size=39,
                                start_date_placeholder_text='Start date',
                                end_date_placeholder_text='End date',
                                clearable=True,
                                min_date_allowed=dt(2001, 1, 1).date(),
                                max_date_allowed=date.today(),
                                start_date=date.today() - timedelta(days=7),
                                end_date=date.today() - timedelta(days=1),
                                initial_visible_month=dt.today().date(),
                                display_format='MMM DD, YY',
                                month_format='MMM YYYY',
                                minimum_nights=2,
                                persistence=True,
                                persisted_props=['start_date', 'end_date'],
                                persistence_type='memory',
                                updatemode='singledate',
                                with_portal=False,
                                style={'margin-left': "20%",
                                       'width': '100%', 'fontsize':6}
                                ),
            dcc.Graph(id='surface_line'),
            dcc.Graph(id='root_zone_line'),
            dcc.Graph(id='7d_each')
        ],style={'width': "50%"})

    ])
])


# ------ CALLBACK --------------------------------------------
# ------ MAP ------- MAP -------- MAP ---------
@app.callback(
    Output(component_id='AL_map',component_property='figure'),
    [Input(component_id='station_type',component_property='value'),
    Input(component_id='my_date_picker_range', component_property='start_date'),
    Input(component_id='my_date_picker_range', component_property='end_date')]
)

def update_map(station_type, start_Date, end_Date):
    if station_type == 'All Stations':
        df = compare.copy()
    else:
        df = compare[compare['station_type'] == station_type].copy()
    temp = df.set_index('station')
    i_list = temp.index.values.tolist()

    # Need avg values for dates between the selected dates
    start_date = dt.strptime(start_Date, '%Y-%m-%d').date()
    end_date = dt.strptime(end_Date, '%Y-%m-%d').date()
    MAP_df = master_df.copy()
    MAP_df['Date'] = MAP_df['Date'].dt.date
    map_df = MAP_df[(MAP_df['Date'] >= start_date) & (MAP_df['Date'] <= end_date)]
    map_mean = map_df.groupby('station')['5cm_7d', '10cm_7d', '20cm_7d', '50cm_7d', '100cm_7d'].mean().reset_index()
    print(map_mean.shape)
    print(map_mean)
    map_mean['all_mean'] = map_mean[['5cm_7d', '10cm_7d', '20cm_7d', '50cm_7d', '100cm_7d']].mean(axis=1)
    map_mean['all_count'] = map_mean[['5cm_7d', '10cm_7d', '20cm_7d', '50cm_7d', '100cm_7d']].count(axis=1)

    # merge this with the metadata
    df_2 = pd.merge(map_mean, df, on='station', how='right').reset_index()
    #print('My map df is: {}'.format(df.shape))
    #print('My map df station type is: {}'.format(station_type))
    print('here is our new map dataframe for crying out loud!')
    print(df_2.shape)
    print(df_2.columns)
    print(df_2.head())
    df_2.set_index('station', inplace=True)


    fig = go.Figure()
    trace = go.Scattermapbox(
        lon=df_2['longitude'],
        lat=df_2['latitude'],
        mode='markers',
        marker=dict(cmax=45,
                    cmin=0,
                    size=12,
                    color=df_2['all_mean'],
                    colorscale= 'Jet',
                    reversescale=True,
                    showscale=True),
        unselected={'marker': {'opacity': 1}},
        selected={'marker': {'opacity': 0.5, 'size': 25}},
        hoverinfo='text',
        customdata=df_2.index,
        text=[df_2.index[i] + '<br><br>lon: ' + str(df_2['longitude'][i]) + '<br>lat: ' + str(
            df_2['latitude'][i]) +  '<br>mean_sm: ' + str( round(df_2['all_mean'][i],2)) + '<br>depths: ' + str(df_2['all_count'][i]) + '<br>start date: ' + str(df_2['startDate'][i]).split(' ')[0] for i in
              range(0, len(i_list))]
    )
    layout = dict(
        clickmode='event+select',
        uirevision='foo',
        hovermode='closest',
        hoverdistance=3,
        autosize=False,
        width=550,
        height=800,
        title=dict(text='Click on site to update graphs.<br>Reclick after using dropdown above.', font=dict(size=20, color='black')),
        mapbox=dict(
            accesstoken=mapbox_access_token,
            style='light',
            center=dict(
                lat=32.7119,
                lon=-86.67348
            ),
            zoom=6
        )
    )
    fig.add_trace(trace)
    fig.update_layout(layout)

    return fig


# --------- LINE GRAPH and BOXPLOT------------------------------------------
@app.callback(
    output = [Output(component_id='surface_line', component_property='figure'),
              Output(component_id='root_zone_line', component_property='figure'),
              Output(component_id='7d_each', component_property='figure')],
    inputs= [Input(component_id='my_date_picker_range', component_property='start_date'),
             Input(component_id='my_date_picker_range', component_property='end_date'),
             Input(component_id='AL_map', component_property='clickData')])

def update_graph(start_Date, end_Date, stn):
    start_date = dt.strptime(start_Date, '%Y-%m-%d').date()
    end_date = dt.strptime(end_Date, '%Y-%m-%d').date()
    print('the start date data type is {}'.format(type(start_date)))
    print(start_date)
    if stn is None:
        # This sets the default if no selection is made
        station = 'AL_Gadsden_19_N'
    else:
        # stn output from the map click is as follows:
        # piggy = {'points': [{'curveNumber': 0, 'pointNumber': 5, 'pointIndex': 5, 'lon': -86.79897, 'lat': 34.19492, 'customdata': '2113:AL:SCAN', 'text': '2113:AL:SCAN<br><br>lon: -86.79897<br>lat: 34.19492<br>start date: 2006-05-18'}]}
        # first item in the customdata is the station name
        station = stn['points'][0]['customdata']
    print('My custom data is: {}'.format(station))
    # Get selected station from the correct df (CRN, SCAN, or new test probe)
    df = master_df[master_df['station']==station]
    # creating month-day column for downstream avg. calculations
    df['mo_day'] = df['Date'].dt.strftime('%m-%d')
    #print(df.head())
    # reset the date datatype:
    df['Date'] = df['Date'].dt.date

    # get just dates selected
    df_dates_selected = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
    print('dates selected df: {}'.format(df_dates_selected.shape))
    # get all unique mo_day; this will be used to get averages across all years
    select_mo_day = df_dates_selected['mo_day'].unique().tolist()
    print('your month days are: ')
    print(select_mo_day)
    print(len(select_mo_day))

    # Get percentiles (10,25,80,95), min, and max for all possible times
    my_surfaces = df.groupby('mo_day')['surface_7d_mean'].describe(percentiles=[0.05, 0.1, 0.25, 0.75, 0.8, 0.95]).reset_index()
    my_roots = df.groupby('mo_day')['root_7d_mean'].describe(percentiles=[0.05, 0.1, 0.25, 0.75, 0.8, 0.95]).reset_index()
    my_surf = my_surfaces[my_surfaces['mo_day'].isin(select_mo_day)].copy()
    my_rut = my_roots[my_roots['mo_day'].isin(select_mo_day)].copy()
    # need to put year back in for mo_day to match that of selection
    date_df = df_dates_selected[['Date', 'mo_day']]
    my_root = pd.merge(my_rut, date_df, on='mo_day', how='left')
    #print('your roots are')
    #print(my_root.shape)
    #print(my_root.head())
    #print('your surface is')

    my_surface = pd.merge(my_surf, date_df, on='mo_day', how='left')
    #print(my_surface.shape)
    #print(my_surface.head())
    #my_root['Date'] = my_root['Date'].dt.date

    # 7-d current
    my_current = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
    print('my current df')
    print(my_current.columns)
    print(my_current.head())
    surface_line = filled_line_graph(my_surface, my_current, 'surface', station)
    root_line = filled_line_graph(my_root, my_current, 'root layer', station)

    # -------- 7d rolling avg line graph ----
    depths = ['5cm_7d', '10cm_7d', '20cm_7d', '50cm_7d', '100cm_7d']
    # get avgs across all years for each of the 5 depths
    all_line = go.Figure()
    # Create and style traces
    for i in range(0,len(depths)):
        col = depths[i]
        hue = str(colors[i])
        my_a = df.groupby('mo_day')[col].mean().reset_index()
        my_av = my_a[my_a['mo_day'].isin(select_mo_day)].copy()
        my_avg = pd.merge(my_av, date_df, on='mo_day', how='left')

        # In case there is no current data:
        all_line.add_trace(go.Scatter(x=my_current['Date'], y=my_current[col], name=col,mode='lines+markers',line=dict(color=hue, width=2)))
        all_line.add_trace(go.Scatter(x=my_avg['Date'], y=my_avg[col],
                                 name = col + " avg.",opacity=.5, line=dict(color=colors[i], width=1, dash='dash'), marker = dict(size = 8, color = colors[i], symbol = 'cross')))

    # dash options include 'dash', 'dot', and 'dashdot'
    # Edit the layout
    #"<b>"+station+"<b>"
    min_dt = df['Date'].min()
    container = 'Earliest date with data: {}'.format(min_dt)
    all_line.update_layout(title={'text': container + "<br><br><b>"+station+"<b>", 'y':0.9,'x':0.5,
                       'xanchor': 'center','yanchor': 'top', "font_size":20},
                      xaxis_title='', yaxis_title='Soil Moisture %')

    return surface_line, root_line, all_line

if __name__ == '__main__':
    app.run_server(debug=False)
