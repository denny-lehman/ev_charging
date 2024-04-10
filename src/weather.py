import requests
import pandas as pd
import numpy as np
import time
import streamlit as st
@st.cache_data
def get_grid_points(latitude, longitude):
    url = f'https://api.weather.gov/points/{latitude},{longitude}'
    print(url)

    r = requests.get(url, timeout=60)

    print('status code:', r.status_code)
    payload = r.json()

    grid_id = payload['properties']['gridId']
    grid_x = payload['properties']['gridX']
    grid_y = r.json()['properties']['gridY']
    return grid_id, grid_x, grid_y

@st.cache_data
def get_weather_forecast(office, grid_x, grid_y):
    url = f'https://api.weather.gov/gridpoints/{office}/{grid_x},{grid_y}/forecast'
    print(url)
    r = requests.get(url, headers={'Accept': 'application/geo+json'}, timeout=60)
    if r.status_code != 200:
        for i in range(2):
            time.sleep(0.3)
            r = requests.get(url, headers={'Accept': 'application/geo+json'})
            if r.status_code == 200:
                break
        if r.status_code != 200:
            print('Failed to get weather forecast')
            return None
    return r.json()

@st.cache_data
def get_hourly_weather_forecast(office, grid_x, grid_y):
    url = f'https://api.weather.gov/gridpoints/{office}/{grid_x},{grid_y}/forecast/hourly'
    print(url)
    r = requests.get(url, headers={'Accept': 'application/geo+json'}, timeout=60)
    if r.status_code != 200:
        for i in range(2):
            time.sleep(0.3)
            r = requests.get(url, headers={'Accept': 'application/geo+json'})
            if r.status_code == 200:
                break
        if r.status_code != 200:
            print('Failed to get weather forecast')
            return None
    return r.json()

@st.cache_data
def get_raw_weather_forecast(office, grid_x, grid_y):
    url = f'https://api.weather.gov/gridpoints/{office}/{grid_x},{grid_y}'
    print(url)
    r = requests.get(url, headers={'Accept': 'application/geo+json'}, timeout=60)
    if r.status_code != 200:
        for i in range(2):
            time.sleep(0.3)
            r = requests.get(url, headers={'Accept': 'application/geo+json'})
            if r.status_code == 200:
                break
        if r.status_code != 200:
            print('Failed to get weather forecast')
            return None
    return r.json()

@st.cache_data
def create_forecast_df(json_forecast):
    forecast = json_forecast['properties']['periods']
    forecast_df = pd.DataFrame(forecast)
    forecast_df['startTime'] = pd.to_datetime(forecast_df['startTime'], utc=True)
    forecast_df['endTime'] = pd.to_datetime(forecast_df['endTime'], utc=True)
    return forecast_df

@st.cache_data
def create_hourly_forecast_df(json_forecast):
    # grab each hourly entry in the forecast
    forecast = json_forecast['properties']['periods']
    forecast_df = pd.DataFrame(forecast)

    # convert startTime to UTC datetime and set as index
    forecast_df['time'] = pd.to_datetime(forecast_df['startTime'])#, utc=True)
    forecast_df = forecast_df.set_index('time')

    # convert temperature to degF and degC
    forecast_df.rename(columns={'temperature': 'temperature_degF'}, inplace=True)
    forecast_df['temperature_degC'] = forecast_df['temperature_degF'].apply(lambda x: np.round((x - 32) * 5.0 / 9.0, 2))

    # convert dewpoint temperature to degF and degC
    forecast_df['dewpoint_degC'] = forecast_df['dewpoint'].apply(lambda x: np.round(x['value'], 2))
    forecast_df['dewpoint_degF'] = forecast_df['dewpoint_degC'].apply(lambda x: np.round(x * 9.0 / 5.0 + 32, 2))

    # extract value from windSpeed column and convert to int
    forecast_df['wind_speed_mph'] = forecast_df['windSpeed'].apply(lambda x: int(x.split(" mph")[0]))

    # extract value from json formatted columns
    forecast_df['probabilityOfPrecipitationPercent'] = forecast_df['probabilityOfPrecipitation'].apply(
        lambda x: x['value'])
    forecast_df['relative_humidity_%'] = forecast_df['relativeHumidity'].apply(lambda x: x['value'])

    # drop columns that are no longer needed
    return forecast_df.drop(
        columns=['startTime', 'endTime', 'windSpeed', 'number', 'name', 'detailedForecast', 'dewpoint',
                 'probabilityOfPrecipitation', 'relativeHumidity', 'temperatureTrend', 'temperatureUnit'])
@st.cache_data
def get_processed_hourly_7day_weather(latitude:float, longitude:float, test_mode:bool=False) -> pd.DataFrame:
    """given the latitude and longitude of a site, return a processed dataframe of the hourly weather. This is a orchestrator function
    args:
        latitude: float - the latitude of the site
        longitude: float - the longitude of the site
        test_mode: bool - if test mode is true, pull stored data from disk, otherwise call the apis
    returns
        weather_df: pd.DataFrame - the processed dataframe of the hourly 7day weather for that site
    """
    if test_mode:
        return pd.DataFrame({})
    office, grid_x, grid_y = get_grid_points(latitude, longitude)
    weather_json = get_hourly_weather_forecast(office, grid_x, grid_y)
    weather_df = create_hourly_forecast_df(weather_json)
    return weather_df