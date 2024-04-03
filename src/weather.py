import requests
import pandas as pd


def get_grid_points(latitude, longitude):
    url = f'https://api.weather.gov/points/{latitude},{longitude}'
    print(url)

    r = requests.get(url)

    print('status code:', r.status_code)
    payload = r.json()

    grid_id = payload['properties']['grid_id']
    grid_x = payload['properties']['grid_x']
    grid_y = r.json()['properties']['grid_y']
    return grid_id, grid_x, grid_y


def get_weather_forecast(office, grid_x, grid_y):
    url = f'https://api.weather.gov/gridpoints/{office}/{grid_x},{grid_y}/forecast'
    print(url)
    r = requests.get(url)
    return r.json()


def get_hourly_weather_forecast(office, grid_x, grid_y):
    url = f'https://api.weather.gov/gridpoints/{office}/{grid_x},{grid_y}/forecast/hourly'
    print(url)
    r = requests.get(url)
    return r.json()


def get_raw_weather_forecast(office, grid_x, grid_y):
    url = f'https://api.weather.gov/gridpoints/{office}/{grid_x},{grid_y}'
    print(url)
    r = requests.get(url)
    return r.json()


def create_hourly_forecast_df(json_forecast):
    forecast = json_forecast['properties']['periods']
    forecast_df = pd.DataFrame(forecast)
    return forecast_df
