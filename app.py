import streamlit as st
import pandas as pd
import numpy as np
import time
import datetime
import pickle
import logging
import altair as alt
from datetime import datetime
from src.data_preprocessing import datetime_processing, userinput_processing, holiday_processing, create_x, \
    create_wide_y
import src.weather as w
import src.oasis as o

import logging
logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)


print("---------------------------")
app_logger = logging.getLogger()
app_logger.addHandler(logging.StreamHandler())
app_logger.setLevel(logging.INFO)
app_logger.info("best")
print("---------------------------")
logger.debug('starting app')
test_mode = True
logger.info(f'test mode is {test_mode}')

# define locations
caltech_lat = 34.134785646454844
caltech_lon = -118.11691382579643

jpl_lat = 34.20142342818471
jpl_lon = -118.17126565774107

office_lat = 37.33680466796926
office_lon = -121.90743423142634

# map locations to site names
site_xy = {'Office001': (office_lat, office_lon), 'Caltech': (caltech_lat, caltech_lon), 'JPL': (jpl_lat, jpl_lon)}

# create SystemDemand object
sd = o.SystemDemand()


@st.cache_data
# update to load CAISO data
def load_data():
    df_of = pd.read_parquet('data/ACN-API/office001/').reset_index(drop=True)
    df_of = datetime_processing(df_of)
    df_of = userinput_processing(df_of)
    df_of = holiday_processing(df_of)
    return df_of

@st.cache_resource
def load_model():
    model = pickle.load(open('model.pkl', 'rb'))
    reg_model = pickle.load(open('reg_model.pkl', 'rb'))
    return model, reg_model

sites = ['Office001','Caltech','JPL']
site_ids = [2,1,19]
site2id = { k:v for (k,v) in zip(sites, site_ids)}
#Why are we duplicating this when it is on line
site2latlon = {'Caltech':(34.134785646454844, -118.11691382579643),
               'Office001':(37.33680466796926, -121.90743423142634),
               'JPL':(34.20142342818471, -118.17126565774107)}
# create site list and site2id dictionary
sites = ['Office001', 'Caltech', 'JPL']
site_ids = [2, 1, 19]
site2id = {k: v for (k, v) in zip(sites, site_ids)}
today_forecast, demand_forecast, solar_df, wind_df, pricing = None, None, None, None, None

st.set_page_config(page_title='Charge Buddy', page_icon=':zap:', layout='wide', initial_sidebar_state='auto')

# title in markdown to allow for styling and positioning
st.markdown("<h1 style='text-align: center; color: orange;'>Charge Buddy</h1>", unsafe_allow_html=True)

# creates a horizontal line
st.divider()

# create columns for layout of the app (1st column is 70% of the page, 2nd column is 30%)
col1, col2 = st.columns([0.8, 0.2])

# create a tagline for the app
st.subheader('Helping EV owners find the best time to charge')

# create a sidebar for user input
st.sidebar.title("When and where?")
st.sidebar.subheader('Select charging site')

# create a dropdown menu for the user to select a site
site = st.sidebar.selectbox('Click below to select a charger location',
                            sites, index=1,
                            )

# create a dropdown menu for the user to select a preference
user_preferences = ['No Preference', 'Eco-Friendly', 'Low Cost']
user_preference = st.sidebar.selectbox('Select your preference',
                                       user_preferences, index=0,
                                       )
lat, long = 0, 0
lat, long = site2latlon.get(site)
logger.info(f'lat lon selected: {lat}, {long}')

grid_id, grid_x, grid_y = w.get_grid_points(lat, long)
forecast = w.get_weather_forecast(grid_id, grid_x, grid_y)

today = datetime.today().date()
if forecast:
    forecast_df = w.create_forecast_df(forecast)
    today_forecast = forecast_df.loc[forecast_df['startTime'].dt.date == today]
else:
    today_forecast = None

logger.info(f'todays forecast: {forecast_df.head()}')
forecast_df.to_csv('data/test_forecast.csv')

@st.cache_data
def get_weather(lat, long, test=test_mode):
    if test:
        return pd.read_csv('data/test_forecast')


    grid_id, grid_x, grid_y = w.get_grid_points(lat, long)
    forecast = w.get_weather_forecast(grid_id, grid_x, grid_y)

    today = datetime.today().date()
    if forecast:
        forecast_df = w.create_forecast_df(forecast)
        today_forecast = forecast_df.loc[forecast_df['startTime'].dt.date == today]
        return forecast_df
    else:
        today_forecast = None


st.sidebar.subheader('Select date')
start_date = st.sidebar.date_input("Start date", value=today)
end_date = st.sidebar.date_input("End date", value=today + pd.Timedelta('1d'))
s_ls = [int(x) for x in str(start_date).split('-')]
e_ls = [int(x) for x in str(end_date).split('-')]
start, end = datetime(s_ls[0], s_ls[1], s_ls[2]), datetime(e_ls[0], e_ls[1], e_ls[2])


def get_tou_pricing(site, start, end):
    pricing = pd.DataFrame(index=pd.date_range(start, end, inclusive='both', freq='h', tz=0), columns=['price'])
    if site == 'Office001':
        for i in list(pricing.index):
            # super off-peak
            if i.hour in range(9, 14):
                pricing.loc[i, 'price'] = 0.18
            # peak
            elif i.hour in range(16, 22):
                pricing.loc[i, 'price'] = 0.40
            # off-peak
            else:
                pricing.loc[i, 'price'] = 0.20
    else:
        for i in list(pricing.index):
            # super off-peak
            if i.hour in range(9, 14):
                pricing.loc[i, 'price'] = 0.12
            # peak
            elif i.hour in range(16, 22):
                pricing.loc[i, 'price'] = 0.40
            # off-peak
            else:
                pricing.loc[i, 'price'] = 0.14

    return pricing


# function to get all forecasts for each site at session start. to be used after introducting statefulness into the app
# def get_forecasts(site):
#     lat, long = site_xy[site]
#     grid_id, grid_x, grid_y = w.get_grid_points(lat, long)
#     forecast = w.get_weather_forecast(grid_id, grid_x, grid_y)
#
#     # added this if-else because the forecast request kept failing
#     if forecast:
#         forecast_df = w.create_forecast_df(forecast)
#         today_forecast = forecast_df.loc[forecast_df['startTime'].dt.date == today]
#     else:
#         today_forecast = None
#
#     # adding logic to prevent redundant API calls since Caltech and JPL are in the same location
#     if site != 'JPL':
#         demand_forecast = sd.get_demand_forecast(start, end)
#         wind_solar_forecast = sd.get_wind_and_solar_forecast(start, end)
#         wind_solar_forecast['INTERVALSTARTTIME_GMT'] = pd.to_datetime(wind_solar_forecast['INTERVALSTARTTIME_GMT'],
#                                                                       utc=True)
#         solar_df = wind_solar_forecast[wind_solar_forecast['RENEWABLE_TYPE'] == 'Solar']
#         wind_df = wind_solar_forecast[wind_solar_forecast['RENEWABLE_TYPE'] == 'Wind']
#         st.session_state[f'{site}_today_forecast'] = today_forecast
#         st.session_state[f'{site}_demand_forecast'] = demand_forecast
#         st.session_state[f'{site}_solar_df'] = solar_df
#         st.session_state[f'{site}_wind_df'] = wind_df
#
#     else:
#         demand_forecast = st.session_state['Caltech_demand_forecast']
#         solar_df = st.session_state['Caltech_solar_df']
#         wind_df = st.session_state['Caltech_wind_df']
#     return today_forecast, demand_forecast, solar_df, wind_df
#
#
def try_forecast(site):
    today_forecast, demand_forecast, solar_df, wind_df = get_forecasts(site)
    today_forecast, demand_forecast, solar_df, wind_df = st.session_state[f'today_forecast'], \
        st.session_state[f'demand_forecast'], \
        st.session_state[f'solar_df'], \
        st.session_state[f'wind_df']

    # if 'key' not in st.session_state:
    #     st.session_state.key = 0
    #     for site in sites:
    #         try_forecast(site)
    # else:
    #     # print(st.session_state.key)
    #     # if any(st.session_state[f'{site}_today_forecast'] is None for site in sites):
    #     #    for site in sites:
    #     #        try_forecast(site)
    #     # else:
    #     today_forecast, demand_forecast, solar_df, wind_df = st.session_state[f'{site}_today_forecast'], \
    #         st.session_state[f'{site}_demand_forecast'], \
    #         st.session_state[f'{site}_solar_df'], \
    #         st.session_state[f'{site}_wind_df']

#if user_preference == 'Eco-Friendly':
#    demand_forecast = sd.get_demand_forecast(start, end)
#    wind_solar_forecast = sd.get_wind_and_solar_forecast(start, end)
#    wind_solar_forecast['INTERVALSTARTTIME_GMT'] = pd.to_datetime(wind_solar_forecast['INTERVALSTARTTIME_GMT'],
#                                                                  utc=True)
#    solar_df = wind_solar_forecast[wind_solar_forecast['RENEWABLE_TYPE'] == 'Solar']
#    wind_df = wind_solar_forecast[wind_solar_forecast['RENEWABLE_TYPE'] == 'Wind']


#st.sidebar.info('EDIT ME: This app is a simple example of '
#                 'using Streamlit to create a financial data web app.\n'
#                 '\nIt is maintained by [Paduel]('
#                 'https://twitter.com/paduel_py).\n\n'
#                 'Check the code at https://github.com/paduel/streamlit_finance_chart')

pricing = get_tou_pricing(site, start, end)
# populate main column with availability chart
col1.column_config = {'justify': 'center'}
with col1:
    st.markdown(f"<h2 style='text-align: center; color: white;'>Availability at {site} </h2>",
                unsafe_allow_html=True)
    #st.subheader(f'Availability at {site}')

    #model = pickle.load(open('reg_model.pkl', 'rb'))
    model, reg_model = load_model()

    st.write('Availability from ', start_date, ' to ', end_date)

    X = pd.DataFrame(index=pd.date_range(start_date, end_date, inclusive='both', freq='h', tz=0),
                     columns=['dow', 'hour', 'month', 'siteID'])

    X['dow'] = X.index.dayofweek
    X['hour'] = X.index.hour
    X['month'] = X.index.month
    X['connectionTime'] = X.index
    X = holiday_processing(X).drop(columns=['connectionTime'])
    X['siteID'] = site2id[site]
    prediction = pd.Series(model.predict(X) * 100, index=X.index, name='% available')

    # regression messes up sometimes, bound the values between [0, 100]
    prediction[prediction > 100] = 100
    prediction[prediction < 0] = 0

    X['% available'] = prediction

    brush = alt.selection(type='interval', encodings=['x'])
    solar_brush = alt.selection(type='interval', encodings=['x'])

    availability_chart = alt.Chart(X.reset_index()).mark_bar(size=15).encode(
        x=alt.X('index', title='Time'),
        y=alt.Y('% available', title='Availability (%)'),
        tooltip=[alt.Tooltip('index', title='Time'),
                 alt.Tooltip('% available', title='Availability (%)')],
        color=alt.condition(brush, alt.value('steelblue'), alt.value('lightgray'))
    ).properties(
        width=1000,
        height=250
    ).add_params(brush)

    pricing_chart = alt.Chart(pricing.reset_index(), title='Pricing').mark_line().encode(
        x=alt.X('index', title='Time'),
        y=alt.Y('price', title='Price ($/kWh)'),
        tooltip=[alt.Tooltip('index', title='Time'),
                 alt.Tooltip('price', title='Price ($/kWh)')],
        color=alt.condition(brush, alt.value('steelblue'), alt.value('lightgray'))
    ).properties(
        width=1000,
        height=250
    ).add_params(brush).transform_filter(brush)

    solar_chart = alt.Chart(solar_df.reset_index(), title='Solar Energy Forecast').mark_bar(size=15).encode(
        x=alt.X('INTERVALSTARTTIME_GMT', title='Time'),
        y=alt.Y('MW', title='Solar Power (MW)'),
        tooltip=[alt.Tooltip('INTERVALSTARTTIME_GMT', title='Time'),
                 alt.Tooltip('MW', title='Solar Power Availabile (MW)')],
        color=alt.condition(solar_brush, alt.value('green'), alt.value('lightgray'))
    ).properties(
        width=1000,
        height=250
    ).add_params(solar_brush)
    if eco & cost:
        st.altair_chart(alt.vconcat(availability_chart, pricing_chart, solar_chart).resolve_scale(x='shared'))
    elif eco:
        st.altair_chart(alt.vconcat(availability_chart, solar_chart).resolve_scale(x='shared'))
    elif cost:
        st.altair_chart(alt.vconcat(availability_chart, pricing_chart).resolve_scale(x='shared'))
    else:
        st.altair_chart(availability_chart)

    availability = ['Very Available', 'Moderate', 'Busy', 'Very Busy']

    st.subheader(f'How often are spots available at {site}?')
    avg_availability = np.round(X['% available'].mean(), 1)

    availability_txt = ''
    if avg_availability > 90:
        availability_txt = availability[0]
    elif avg_availability > 70:
        availability_txt = availability[1]
    elif avg_availability > 50:
        availability_txt = availability[2]
    else:
        availability_txt = availability[3]
    st.text(f'{availability_txt}. Average availability: ' + str(avg_availability) + '%')
    st.text('More locations coming soon!')

col2.column_config = {'justify': 'right'}
with col2:
    st.markdown(f"<h3 style='text-align: center; color: white;'>Weather Forecast for {site} {today_forecast['name'].iloc[0]} </h3>",
                unsafe_allow_html=True)
    col2_1, col2_2 = st.columns([0.5, 0.5])
    if today_forecast is not None:
        col2_1.metric('Temperature (F)', today_forecast['temperature'].iloc[0])
        col2_2.image(today_forecast['icon'].iloc[0], use_column_width=False)
        col2_1.write(today_forecast['detailedForecast'].iloc[0])
    else:
        col2_1.write('Unable to retrieve forecast data')
        if col2_1.button('Retry'):
            try_forecast(site)
