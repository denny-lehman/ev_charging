import requests
import pandas as pd
import numpy as np
import time
import streamlit as st
from typing import Tuple, Dict

import logging
logger = logging.getLogger(__name__)

@st.cache_data
def get_grid_points(latitude:float, longitude:float)->Tuple[str, int, int]:
    """The way the weather api system works is by finding the station's grid points that are closest to the lat long coordinates. The code below gets the grid x and grid y from the lat long coordinates
    inputs:
        latitude: float - the latitude coordinate of the desired weather location
        longitude: float - the longitude coordinate of the desired weather location
    returns:
        (grid_id, grid_x, grid_y) tuple of the office id, and x and y grid coordinates needed for future weather.gov api calls
    > get_grid_points(34.134785646454844, -118.11691382579643)
    >('LOX', 160, 48)"""
    url = f'https://api.weather.gov/points/{latitude},{longitude}'
    print('get grid points url:', url)

    r = requests.get(url, timeout=60)

    print('status code:', r.status_code)
    payload = r.json()

    grid_id = payload['properties']['gridId']
    grid_x = payload['properties']['gridX']
    grid_y = r.json()['properties']['gridY']
    return grid_id, grid_x, grid_y

@st.cache_data
def get_weather_forecast(office:str, gridX:int, gridY:int)->Dict:
    """forecast for 12h periods over the next seven days
    args:
        office: str - the 3 letter code for the weather station
        gridX: int - the X coordinate for the weather grid
        gridY: int - the Y coordinate for the weather grid
    returns:
        dict - the json payload
    """
    url = f'https://api.weather.gov/gridpoints/{office}/{gridX},{gridY}/forecast'
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
            return {}
    return r.json()

@st.cache_data
def get_hourly_weather_forecast(office:str, gridX:int, gridY:int) -> Dict:
    """forecast for hourly periods over the next seven days
    args:
        office: str - the 3 letter code for the weather station
        gridX: int - the X coordinate for the weather grid
        gridY: int - the Y coordinate for the weather grid
    returns:
        dict - the json payload
    """
    url = f'https://api.weather.gov/gridpoints/{office}/{gridX},{gridY}/forecast/hourly'
    print(url)
    r = requests.get(url)
    if r.status_code != 200:
        for i in range(2):
            time.sleep(0.3)
            r = requests.get(url, headers={'Accept': 'application/geo+json'})
            if r.status_code == 200:
                break
        if r.status_code != 200:
            print('Failed to get weather forecast')
            return {}
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


def convert_today_weather_to_hourly(half_day_df):
    """convert the half day dataframe and expand it to each hour of the forecast

    > half_day = get_weather_forecast(ct_grid, ct_grid_x, ct_grid_y)
    > full_day = convert_today_weather_to_hourly(half_day)
    > full_day.colums
    > ['temperature', 'dewpoint', 'windSpeed', 'relativeHumidity',
       'probabilityOfPrecipitation', 'time_utc', 'time_local']

    """
    start_date = half_day_df['startTime'].min().date()
    end_date = start_date + pd.Timedelta("1d")
    print(start_date, end_date)
    df = pd.DataFrame(index=pd.date_range(start_date, end_date, inclusive='both', freq='h', tz=0),
                      columns=half_day_df.columns.tolist())
    df['time_utc'] = df.index
    df['time_local'] = df.index.tz_convert('US/Pacific')
    i = 0
    # for each hour in the 24 hour day
    for j in range(len(df)):
        # for each hour, apply the 6 hour forecast to that period

        # get the latest forecast
        if half_day_df.loc[i, 'startTime'] < df.index[j]:
            i += 1
        # apply the forecast in row i to the hourly in row j
        df.loc[pd.to_datetime(df.index)[j], :] = half_day_df.loc[i, :]

    df = convert_weather_values(df)

    return df.iloc[:24] # return only the 24 hour period

def convert_weather_values(forecast_df):
    """converts values of temperature, dew point and others from C to F"""

    assert set(['temperature', 'dewpoint', 'windSpeed', 'probabilityOfPrecipitation', 'relativeHumidity']).issubset(forecast_df.columns), f"missing columns for weather values in forecast_df.columns = {forecast_df.columns}"

    # convert temperature to degF and degC
    forecast_df.rename(columns={'temperature': 'temperature_degF'}, inplace=True)
    forecast_df['temperature_degC'] = forecast_df['temperature_degF'].apply(lambda x: np.round((x - 32) * 5.0 / 9.0, 2))

    # convert dewpoint temperature to degF and degC
    forecast_df['dewpoint_degC'] = forecast_df['dewpoint'].apply(lambda x: np.round(x['value'], 2))
    forecast_df['dewpoint_degF'] = forecast_df['dewpoint_degC'].apply(lambda x: np.round(x * 9.0 / 5.0 + 32, 2))

    # extract value from windSpeed column and convert to int
    forecast_df['wind_speed_mph'] = forecast_df['windSpeed'].apply(lambda x: int(x.split()[0]))

    # extract value from json formatted columns
    forecast_df['probabilityOfPrecipitationPercent'] = forecast_df['probabilityOfPrecipitation'].apply(
        lambda x: x['value'])
    forecast_df['relative_humidity_%'] = forecast_df['relativeHumidity'].apply(lambda x: x['value'])
    return forecast_df

# deprecate
@st.cache_data
def create_forecast_df(json_forecast):
    forecast = json_forecast['properties']['periods']
    forecast_df = pd.DataFrame(forecast)
    forecast_df['startTime'] = pd.to_datetime(forecast_df['startTime'], utc=True)
    forecast_df['endTime'] = pd.to_datetime(forecast_df['endTime'], utc=True)
    return forecast_df

@st.cache_data
def create_hourly_forecast_df(json_forecast:dict)->pd.DataFrame:
    # grab each hourly entry in the forecast
    assert 'properties' in json_forecast.keys()

    forecast = json_forecast['properties']['periods']
    forecast_df = pd.DataFrame(forecast)

    # convert startTime to UTC datetime and set as index
    forecast_df['time_local'] = pd.to_datetime(forecast_df['startTime'], utc=True).dt.tz_convert('US/Pacific')  # , utc=True)
    forecast_df['time_utc'] = pd.to_datetime(forecast_df['startTime'], utc=True)
    forecast_df['time'] = forecast_df['time_utc']
    forecast_df = forecast_df.set_index('time')

    forecast_df = convert_weather_values(forecast_df)


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
        today_weather_df: pd.DataFrame - the forecast used in the dashboard
        weather_df: pd.DataFrame - the processed dataframe of the hourly 7day weather for that site
    """
    logger.info(f'getting weather forecast for lat/long pair {latitude}, {longitude}')
    if test_mode:
        return pd.read_csv('./data/test_forecast.csv')
    office, grid_x, grid_y = get_grid_points(latitude, longitude)
    today_weather_json = get_weather_forecast(office, grid_x, grid_y)
    today_weather_df = create_forecast_df(today_weather_json)
    today_weather_df = convert_today_weather_to_hourly(today_weather_df)
    # today_hourly_weather = create_hourly_forecast_df(today_weather_df)
    logger.info(f'todays weather contains times starting at {today_weather_df.index.min()} through {today_weather_df.index.max()}')
    # today_hourly_weather = convert_weather_values(today_weather_df)

    weather_json = get_hourly_weather_forecast(office, grid_x, grid_y)

    weather_df = create_hourly_forecast_df(weather_json)
    # assert set(today_weather_df.columns).issubset(weather_df.columns), 'columns in today forecast and 7 day forecast dont match'
    weather_df = pd.concat(
        [today_weather_df[today_weather_df.index < weather_df.index.min()] # collect all times less than the 7 day forecast
            , weather_df], axis=0).sort_index()
    return today_weather_df, weather_df

