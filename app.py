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

caltech_lat = 34.134785646454844
caltech_lon = -118.11691382579643

jpl_lat = 34.20142342818471
jpl_lon = -118.17126565774107

office_lat = 37.33680466796926
office_lon = -121.90743423142634

site_xy = {'Office001': (office_lat, office_lon), 'Caltech': (caltech_lat, caltech_lon), 'JPL': (jpl_lat, jpl_lon)}
sd = o.SystemDemand()


@st.cache_data
# update to load CAISO data
def load_data():
    df_of = pd.read_parquet('data/ACN-API/office001/').reset_index(drop=True)
    df_of = datetime_processing(df_of)
    df_of = userinput_processing(df_of)
    df_of = holiday_processing(df_of)
    return df_of


def load_model():
    model = pickle.load(open('model.pkl', 'rb'))
    return model


sites = ['Office001', 'Caltech', 'JPL']
site_ids = [2, 1, 19]
site2id = {k: v for (k, v) in zip(sites, site_ids)}
today_forecast, demand_forecast, solar_df, wind_df = None, None, None, None
st.set_page_config(page_title='Charge Buddy', page_icon=':zap:', layout='wide', initial_sidebar_state='auto')

st.markdown("<h1 style='text-align: center; color: orange;'>Charge Buddy</h1>", unsafe_allow_html=True)
#st.title('Charge Buddy')
st.divider()
col1, col2 = st.columns([0.7, 0.3])
st.subheader('Helping EV owners know when to charge')

st.sidebar.title("When and where?")
st.sidebar.subheader('Select charging site')
site = st.sidebar.selectbox('Click below to select a charger location',
                            sites, index=0,
                            # format_func=label
                            )
user_preferences = ['No Preference', 'Eco-Friendly', 'Low Cost']
user_preference = st.sidebar.selectbox('Select your preference',
                                       user_preferences, index=0,
                                       # format_func=label
                                       )
lat, long = 0, 0
if site == 'Office001':
    lat, long = office_lat, office_lon
elif site == 'Caltech':
    lat, long = caltech_lat, caltech_lon
elif site == 'JPL':
    lat, long = jpl_lat, jpl_lon

grid_id, grid_x, grid_y = w.get_grid_points(lat, long)
forecast = w.get_weather_forecast(grid_id, grid_x, grid_y)

today = datetime.today().date()
if forecast:
    forecast_df = w.create_forecast_df(forecast)
    today_forecast = forecast_df.loc[forecast_df['startTime'].dt.date == today]
else:
    today_forecast = None

st.sidebar.subheader('Select date')
start_date = st.sidebar.date_input("Start date", value=today)
end_date = st.sidebar.date_input("End date", value=today + pd.Timedelta('1d'))
s_ls = [int(x) for x in str(start_date).split('-')]
e_ls = [int(x) for x in str(end_date).split('-')]
start, end = datetime(s_ls[0], s_ls[1], s_ls[2]), datetime(e_ls[0], e_ls[1], e_ls[2])

if 1 == 2:
    # function to get all forecasts for each site at session start. to be used after introducting statefulness into the app
    def get_forecasts(site):
        lat, long = site_xy[site]
        grid_id, grid_x, grid_y = w.get_grid_points(lat, long)
        forecast = w.get_weather_forecast(grid_id, grid_x, grid_y)

        # added this if-else because the forecast request kept failing
        if forecast:
            forecast_df = w.create_forecast_df(forecast)
            today_forecast = forecast_df.loc[forecast_df['startTime'].dt.date == today]
        else:
            today_forecast = None

        demand_forecast = sd.get_demand_forecast(start, end)
        time.sleep(0.3)
        wind_solar_forecast = sd.get_wind_and_solar_forecast(start, end)
        wind_solar_forecast['INTERVALSTARTTIME_GMT'] = pd.to_datetime(wind_solar_forecast['INTERVALSTARTTIME_GMT'],
                                                                      utc=True)
        solar_df = wind_solar_forecast[wind_solar_forecast['RENEWABLE_TYPE'] == 'Solar']
        wind_df = wind_solar_forecast[wind_solar_forecast['RENEWABLE_TYPE'] == 'Wind']
        return today_forecast, demand_forecast, solar_df, wind_df

    def try_forecast(site):
        today_forecast, demand_forecast, solar_df, wind_df = get_forecasts(site)
        st.session_state[f'{site}_today_forecast'] = today_forecast
        st.session_state[f'{site}_demand_forecast'] = demand_forecast
        st.session_state[f'{site}_solar_df'] = solar_df
        st.session_state[f'{site}_wind_df'] = wind_df

    if 'key' not in st.session_state:
        st.session_state.key = 0
        for site in sites:
            try_forecast(site)
        else:
            if any(st.session_state[f'{site}_today_forecast'] is None for site in sites):
                for site in sites:
                    try_forecast(site)
            else:
                today_forecast, demand_forecast, solar_df, wind_df = st.session_state[f'{site}_today_forecast'], \
                    st.session_state[f'{site}_demand_forecast'], \
                    st.session_state[f'{site}_solar_df'], \
                    st.session_state[f'{site}_wind_df']
    print(today_forecast, demand_forecast, solar_df, wind_df)

if user_preference == 'Eco-Friendly':
    demand_forecast = sd.get_demand_forecast(start, end)
    wind_solar_forecast = sd.get_wind_and_solar_forecast(start, end)
    wind_solar_forecast['INTERVALSTARTTIME_GMT'] = pd.to_datetime(wind_solar_forecast['INTERVALSTARTTIME_GMT'],
                                                                  utc=True)
    solar_df = wind_solar_forecast[wind_solar_forecast['RENEWABLE_TYPE'] == 'Solar']
    wind_df = wind_solar_forecast[wind_solar_forecast['RENEWABLE_TYPE'] == 'Wind']
#st.sidebar.button("Run")

# st.sidebar.info('EDIT ME: This app is a simple example of '
#                 'using Strealit to create a financial data web app.\n'
#                 '\nIt is maintained by [Paduel]('
#                 'https://twitter.com/paduel_py).\n\n'
#                 'Check the code at https://github.com/paduel/streamlit_finance_chart')


with col1:
    st.markdown(f"<h2 style='text-align: center; color: white;'>Availability at {site} </h2>",
                unsafe_allow_html=True)
    #st.subheader(f'Availability at {site}')

    model = pickle.load(open('reg_model.pkl', 'rb'))

    st.write(start_date, ' to ', end_date)

    X = pd.DataFrame(index=pd.date_range(start_date, end_date, inclusive='both', freq='h', tz=0),
                     columns=['dow', 'hour', 'month', 'siteID'])
    # X['dow'] = X.index.dt.hour
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

    availability_chart = alt.Chart(X.reset_index()).mark_bar(size=12).encode(
        x=alt.X('index', title='Time'),
        y=alt.Y('% available', title='Availability (%)'),
    ).properties(
        width=600,
        height=300
    )
    if user_preference == 'Eco-Friendly':
        solar_chart = alt.Chart(solar_df, title='Solar Energy Forecast').mark_bar(size=12).encode(
            x=alt.X('INTERVALSTARTTIME_GMT', title='Time'),
            y=alt.Y('MW', title='Solar Power (MW)'),
            tooltip=[alt.Tooltip('INTERVALSTARTTIME_GMT', title='Time'),
                     alt.Tooltip('MW', title='Solar Power Availabile (MW)')]
        ).properties(
            width=600,
            height=300
        )
        combined = alt.vconcat(availability_chart, solar_chart).resolve_scale(x='shared')
        st.altair_chart(combined)
    else:
        st.altair_chart(availability_chart)
        #st.line_chart(solar_df[['INTERVALSTARTTIME_GMT', 'MW']])
    #st.bar_chart(X, x=None, y='% available', width=0)

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

col2.column_config = {'justify': 'center'}
with col2:
    st.markdown(f"<h3 style='text-align: center; color: white;'>Today's Weather Forecast for {site} </h3>",
                unsafe_allow_html=True)
    col2_1, col2_2 = st.columns([0.7, 0.3])
    if today_forecast is not None:
        col2_1.metric('Temperature (F)', today_forecast['temperature'].iloc[0])
        col2_2.image(today_forecast['icon'].iloc[0], use_column_width=False)
        col2_1.write(today_forecast['detailedForecast'].iloc[0])
    else:
        col2_1.write('Unable to retrieve forecast data')

# hist_values = np.histogram(y, bins=9, range=(0,9))[0]
# st.bar_chart(hist_values)
