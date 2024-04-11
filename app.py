import streamlit as st
import pandas as pd
import numpy as np
import time
import datetime
import pickle
import logging
import altair as alt
import os
from datetime import datetime
import pytz
import folium
from streamlit_folium import folium_static
from typing import Tuple
print(os.getcwd())
from src.data_preprocessing import datetime_processing, userinput_processing, holiday_processing, create_x, \
            create_wide_y, make_time_features
import src.weather as w
import src.oasis as o
from src.weather import get_processed_hourly_7day_weather
import logging

from streamlit_geolocation import streamlit_geolocation
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


print("---------------------------")
# app_logger = logging.getLogger()
# app_logger.addHandler(logging.StreamHandler())
# app_logger.setLevel(logging.INFO)
# app_logger.info("best")
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


# create SystemDemand object
sd = o.SystemDemand()

#get today's datetime
today = datetime.today().date()

# @st.cache_data
# to load CAISO data
# def load_data():
    # df_of = pd.read_parquet('data/ACN-API/office001/').reset_index(drop=True)
    # df_of = datetime_processing(df_of)
    # df_of = userinput_processing(df_of)
    # df_of = holiday_processing(df_of)
    # return df_of

@st.cache_resource
def load_model():
    model = pickle.load(open('models/model.pkl', 'rb'))
    model_final = pickle.load(open('models/model_04_10.pkl', 'rb'))
    reg_model = pickle.load(open('models/reg_model.pkl', 'rb'))
    return model, model_final, reg_model

@st.cache_data
def get_weather(lat:float, long:float, test:bool=test_mode) -> pd.DataFrame:
    logger.info(f'getting weather forecast for lat/long pair {lat}, {long}')
    if test:
        logger.info('In test mode: skipping api call, returning test dataframe')
        return pd.read_csv('data/test_forecast.csv')

    logger.info('calling weather forecast APIs')
    grid_id, grid_x, grid_y = w.get_grid_points(lat, long)
    forecast = w.get_weather_forecast(grid_id, grid_x, grid_y)

    # TODO: fix this part. We need Today's forecast, so it should be returned or handled differently
    if forecast:
        forecast_df = w.create_forecast_df(forecast)
        today_forecast = forecast_df.loc[forecast_df['startTime'].dt.date == today]
    else:
        today_forecast = None
    return forecast_df

def get_tou_pricing(site, start, end, tz='UTC-07:00'):
    pricing = pd.DataFrame(index=pd.date_range(start, end, inclusive='both', freq='h'), columns=['price'])
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
@st.cache_data
def get_forecasts(site:str) -> Tuple[pd.DataFrame]:
    lat, long = site2latlon[site]

    today_forecast = get_weather(lat, long, test=False)

    demand_forecast = sd.get_demand_forecast(range_start, range_end)
    wind_solar_forecast = sd.get_wind_and_solar_forecast(range_start, range_end)
    wind_solar_forecast['INTERVALSTARTTIME_GMT'] = pd.to_datetime(wind_solar_forecast['INTERVALSTARTTIME_GMT'],
                                                                      utc=True)
    solar_df = wind_solar_forecast[wind_solar_forecast['RENEWABLE_TYPE'] == 'Solar']
    wind_df = wind_solar_forecast[wind_solar_forecast['RENEWABLE_TYPE'] == 'Wind']
    return today_forecast, demand_forecast, solar_df, wind_df, wind_solar_forecast

#
# def try_forecast(site:str):
    # today_forecast, demand_forecast, solar_df, wind_df, wind_solar_forecast = get_forecasts(site)
    # st.session_state[f'{site}_today_forecast'] = today_forecast
    # st.session_state[f'{site}_demand_forecast'] = demand_forecast
    # st.session_state[f'{site}_solar_df'] = solar_df
    # st.session_state[f'{site}_wind_df'] = wind_df
    # st.session_state[f'{site}_wind_solar_forecast'] = wind_solar_forecast


sites = ['Office001','Caltech','JPL']
site_ids = [2,1,19]
site2id = { k:v for (k,v) in zip(sites, site_ids)}
#Why are we duplicating this when it is on line
site2latlon = {'Caltech':(34.134785646454844, -118.11691382579643),
               'Office001':(37.33680466796926, -121.90743423142634),
               'JPL':(34.20142342818471, -118.17126565774107)}
# map locations to site names
logger.info(f'loaded site lat and long coordinates: {site2latlon.items()}')

site2tac = {2:'PGE-TAC', 1:'SCE-TAC', 19:'SCE-TAC',}
today_forecast, demand_forecast, solar_df, wind_df, pricing, wind_solar_forecast = None, None, None, None, None, None
logger.info('initialized site variables and maps')

st.set_page_config(page_title='Charge Buddy', page_icon=':zap:', layout='wide', initial_sidebar_state='auto')

# title in markdown to allow for styling and positioning
st.markdown("<h1 style='text-align: center; color: orange;'>Charge Buddy</h1>", unsafe_allow_html=True)

# creates a horizontal line
st.divider()

# create columns for layout of the app (1st column is 70% of the page, 2nd column is 30%)
col1, col2 = st.columns([0.7, 0.3])

# create a tagline for the app
st.subheader('Helping EV owners find the best time to charge')

# create a sidebar for user input
st.sidebar.title("When and where?")
st.sidebar.subheader('Select charging site')

# create a dropdown menu for the user to select a site
site = st.sidebar.selectbox('Click below to select a charger location',
                            sites, index=1,
                            key='site' # adds the site to the session state
                            )
logger.info(f'site selected: {st.session_state["site"]}')


st.sidebar.subheader('Select your preference')
eco = st.sidebar.checkbox('Eco-Friendly', key='eco')
cost = st.sidebar.checkbox('Low Cost', key='cost')
logger.info(f'eco selected: {st.session_state["eco"]}\nlow cost selected: {st.session_state["cost"]}')

lat, long = 0, 0
lat, long = site2latlon.get(site)
logger.info(f'lat lon selected: {lat}, {long}')

forecast_df = get_weather(lat, long, test=False)
logger.info(f'todays forecast: {forecast_df.head()}')
forecast_df.to_csv('data/test_forecast.csv')

st.sidebar.subheader('Select date')
start_date = st.sidebar.date_input("Start date", value=today, min_value=today, max_value=today + pd.Timedelta('6d'), key='start')
end_date = st.sidebar.date_input("End date", value=start_date + pd.Timedelta('1d'), max_value=today + pd.Timedelta('7d'), key='end')
logger.info(f'date range selected is: {st.session_state["start"]} - {st.session_state["end"]}')
s_ls = [int(x) for x in str(start_date).split('-')]
e_ls = [int(x) for x in str(end_date).split('-')]
start_localized, end_localized = pytz.utc.localize(datetime(s_ls[0], s_ls[1], s_ls[2])), pytz.utc.localize(datetime(e_ls[0], e_ls[1], e_ls[2]))
if 'start' not in st.session_state.keys():
    st.session_state['start'] = start_localized
if 'end' not in st.session_state.keys():
    st.session_state['end'] =  end_localized
logger.info(f'date range localized is: {st.session_state["start"]} - {st.session_state["end"]}')

range_start_ls = [int(x) for x in str(today).split('-')]
range_end_ls = [int(x) for x in str(today + pd.Timedelta('7d')).split('-')]
range_start = datetime(range_start_ls[0], range_start_ls[1], range_start_ls[2])
range_end = datetime(range_end_ls[0], range_end_ls[1], range_end_ls[2])

with st.sidebar:
    loc = streamlit_geolocation()
    st.write(f"Current Location: {loc}")



# TODO: is this a switch?

st.session_state.key = 0
today_forecast, demand_forecast, solar_df, wind_df, wind_solar_forecast = get_forecasts(st.session_state.site)



#st.sidebar.info('EDIT ME: This app is a simple example of '
#                 'using Streamlit to create a financial data web app.\n'
#                 '\nIt is maintained by [Paduel]('
#                 'https://twitter.com/paduel_py).\n\n'
#                 'Check the code at https://github.com/paduel/streamlit_finance_chart')

pricing = get_tou_pricing(site, start_localized, end_localized)
# populate main column with availability chart
col1.column_config = {'justify': 'center'}
with col1:
    st.markdown(f"<h2 style='text-align: center; color: white;'>Availability at {site} </h2>",
                unsafe_allow_html=True)
    model, model_final, reg_model = load_model()

    st.write('Availability from ', start_date, ' to ', end_date)

    # get time, demand, and weather features
    # combine the 3 feature sets
    # perform inference
    
    logger.info(f'start date type {type(start_localized)} and value is {start_localized}')
    time_df = make_time_features(start_date, end_date)
    time_df['site'] = st.session_state['site']

    assert {'site', 'index'}.issubset(time_df.reset_index().columns)


    future_weather = get_processed_hourly_7day_weather(*site2latlon[st.session_state['site']])
    m = folium.Map(location=[*site2latlon[st.session_state['site']]], zoom_start=5)
    folium.Marker(
            location=[*site2latlon[st.session_state['site']]],
            popup=f"{st.session_state['site']}",
            icon=folium.Icon(color="green")
    ).add_to(m)
    future_weather['site'] = st.session_state['site']

    assert {'site', 'time'}.issubset(future_weather.reset_index().columns)

    #demand_forecast = st.session_state[f'{site}_demand_forecast']
    logger.info(f'demand forecast loaded with shape {demand_forecast.shape} and columns: {demand_forecast.columns}')
    demand_forecast['datetime'] = pd.to_datetime(demand_forecast['OPR_DT']) + pd.to_timedelta(demand_forecast['OPR_HR'], unit='h')
    demand = demand_forecast.loc[
        demand_forecast['TAC_AREA_NAME'] == site2tac[site2id[site]], :].set_index('datetime')

    demand['site'] =  st.session_state['site']
    demand = demand.rename(columns={'MW': 'actual_demand_MW'}).sort_index()
    demand.index = demand.index.tz_localize('UTC-07:00')


    logger.info(f'demand loaded with shape {demand.shape} and columns: {demand.columns}')
    print(demand.reset_index().head())
    assert 'site' in demand.columns and 'datetime' in demand.reset_index().columns

    # combine
    features = ['dow', 'hour', 'month', 'is_holiday', 'actual_demand_MW',
                'temperature_degC', 'dewpoint_degC', 'relative_humidity_%',
                           'wind_speed_mph', 'site']
    X = pd.DataFrame({}, columns=features)
    try:
        X = pd.merge(time_df.reset_index(), demand.reset_index(), how='left', left_on=['index', 'site'],
                       right_on=['datetime', 'site'])
    except:
        assert 1==0, 'failed to merge time_df and demand'
    try:
        X = pd.merge(X, future_weather.reset_index(), how='left', left_on=['index', 'site'],
                       right_on=['time', 'site'])
    except:
        logger.info('failed to merge time, weather, and demand features')
    X.index = X['datetime']
    X = X[features]
    prediction = pd.Series(model_final.predict(X) * 100, index=X.index, name='% available')
    # X = pd.DataFrame(index=pd.date_range(start_date, end_date, inclusive='both', freq='h', tz=0),
    #                      columns=['dow', 'hour', 'month', 'siteID'])
    #
    # X['dow'] = X.index.dayofweek
    # X['hour'] = X.index.hour
    # X['month'] = X.index.month
    # X['connectionTime'] = X.index
    # X = holiday_processing(X).drop(columns=['connectionTime'])
    # X['siteID'] = site2id[site]
    # prediction = pd.Series(reg_model.predict(X) * 100, index=X.index, name='% available')

    # regression messes up sometimes, bound the values between [0, 100]
    prediction[prediction > 100] = 100
    prediction[prediction < 0] = 0

    X['% available'] = prediction

    brush = alt.selection(type='interval', encodings=['x'])
    solar_brush = alt.selection(type='interval', encodings=['x'])
    scale = alt.Scale(domain=[pd.to_datetime(start_localized), pd.to_datetime(end_localized)])
    
    wind_solar_forecast = wind_solar_forecast.sort_values('INTERVALSTARTTIME_GMT').loc[(wind_solar_forecast['INTERVALSTARTTIME_GMT'] >= start_localized) & (wind_solar_forecast['INTERVALSTARTTIME_GMT'] <= end_localized)]
    availability_chart = alt.Chart(X.reset_index()).mark_bar(size=15).encode(
            x=alt.X('datetime:T', title='Time'),
        y=alt.Y('% available', title='Availability (%)'),
        tooltip=[alt.Tooltip('datetime', title='Time'),
                 alt.Tooltip('% available', title='Availability (%)')],
        color=alt.condition(brush, alt.value('steelblue'), alt.value('lightgray'))
    ).properties(
        width=800,
        height=250
    ).add_params(brush)

#logger.info(f'pricing is {pricing.reset_index().info()}')
    pricing_chart = alt.Chart(pricing.reset_index(), title='Pricing').mark_line().encode(
        x=alt.X('index:T', title='Time'),
        y=alt.Y('price', title='Price ($/kWh)'),
        tooltip=[alt.Tooltip('index', title='Time'),
                 alt.Tooltip('price', title='Price ($/kWh)')],
        color=alt.condition(brush, alt.value('steelblue'), alt.value('lightgray'))
    ).properties(
        width=800,
        height=250
    ).add_params(brush).transform_filter(brush)
    if False:
        solar_chart = alt.Chart(solar_df.reset_index(), title='Solar Energy Forecast').mark_bar(size=15).encode(
            x=alt.X('index', title='Time'),
            y=alt.Y('MW', title='Solar Power (MW)'),
            tooltip=[alt.Tooltip('INTERVALSTARTTIME_GMT', title='Time'),
                     alt.Tooltip('MW', title='Solar Power Availabile (MW)')],
            color=alt.condition(solar_brush, alt.value('green'), alt.value('lightgray'))
        ).properties(
            width=800,
            height=250
        ).add_params(solar_brush)

    solar_chart = alt.Chart(wind_solar_forecast, title='Renewable Energy Forecast').mark_bar(size=15).encode(
        x=alt.X('INTERVALSTARTTIME_GMT:T', title='Time'),
        y=alt.Y('MW', title='Solar Power (MW)'),
        tooltip=[alt.Tooltip('INTERVALSTARTTIME_GMT', title='Time'),
                 alt.Tooltip('MW', title='Solar Power Availabile (MW)')],
        color='RENEWABLE_TYPE:N'
    ).properties(
        width=800,
        height=250
    )#.add_params(solar_brush)

    if eco & cost:
        #need to add pricing chart back
        st.altair_chart(alt.vconcat(availability_chart, pricing_chart, solar_chart).resolve_scale(x='shared'))
    elif eco:
        st.altair_chart(alt.vconcat(availability_chart, solar_chart).resolve_scale(x='shared'))
    elif cost:
        #need to add pricing chart back
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
    st.subheader("EV Charging Station Location")
    folium_static(m)