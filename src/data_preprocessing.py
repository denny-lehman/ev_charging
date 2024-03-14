import pandas as pd
import numpy as np
from pandas.tseries.holiday import USFederalHolidayCalendar as calendar

def convert_userInputs(x):
    """could do try except block instead"""
    # x is a string of a list of dictionaries, like this
    # '[{'userID': 333, 'milesRequested': 20, 'WhPerMile': 400, 'minutesAvailable': 277, 'modifiedAt': 'Wed, 05 Sep 2018 11:08:31 GMT', 'paymentRequired': True, 'requestedDeparture': 'Wed, 05 Sep 2018 15...}]'
    if x:
        x = eval(x)  # convert string to list
        x = x[0]  # get first and only entry in list (a dictionary)
        return pd.Series(x)  # convert dictionary to a series
    else:  # x is none
        none_record = {'userID': None,
                       'milesRequested': None,
                       'WhPerMile': None,
                       'minutesAvailable': None,
                       'modifiedAt': None,
                       'paymentRequired': None,
                       'requestedDeparture': None,
                       'kWhRequested': None
                       }
        return pd.Series(none_record)


def userinput_processing(df):
    if 'userInputs' not in df.columns:
        print(f'the column userInputs was not found in the dataframes columns. userinput processing skipped.')
        return df
    assert 'userInputs' in list(df.columns)
    return pd.concat([df.drop(columns='userInputs'), df['userInputs'].apply(convert_userInputs)], axis=1)

def datetime_processing(df):
    df['connectionTime'] = pd.to_datetime(df['connectionTime'], utc=True, errors='coerce')
    df['connectionTimeHour'] = df['connectionTime'].dt.hour
    df['connectionTimeDay'] = df['connectionTime'].dt.day
    df['disconnectTime'] = pd.to_datetime(df['disconnectTime'], utc=True, errors='coerce')
    df['disconnectTimeHour'] = df['disconnectTime'].dt.hour
    df['disconnectTimeDay'] = df['disconnectTime'].dt.day
    df['doneChargingTime'] = pd.to_datetime(df['doneChargingTime'], utc=True, errors='coerce')
    df['doneChargingTimeHour'] = df['doneChargingTime'].dt.hour
    df['doneChargingTimeDay'] = df['doneChargingTime'].dt.day
    return df

########################
## Holiday processing ##
########################
def holiday_processing(df:pd.DataFrame, date_column:str='index')->pd.DataFrame:
    """this function is a wrapper for the holiday_processing_series function.
     This function takes a data frame and returns the dataframe with a new column is_holiday"""
    if date_column == 'index':
        date_series = df.index
    else:
        date_series = df[date_column]

    start = date_series.min()
    end = date_series.max()

    df['is_holiday'] = holiday_processing_series(start, end, date_series)

    return df

def holiday_processing_series(start, end, dates)->np.ndarray:
    """This function returns a true or false if a given date range falls on a holiday"""
    cal = calendar()
    holidays = cal.holidays(start=start, end=end)
    return np.isin(dates.date, holidays.date)


########################
## Create Y values    ##
########################
def create_single_space_y(df, start, end, spaceID):
    tmp = df.copy()
    tmp = tmp[tmp['spaceID'] == spaceID].sort_index()
    y = pd.DataFrame(index=pd.date_range(start, end, inclusive='both', freq='h', tz=0),
                     columns=['is_available'])
    y['is_available'] = 1
    tmp.reset_index(inplace=True)
    for i in list(tmp.index):
        start_ = tmp.loc[i, 'connectionTime']
        end_ = tmp.loc[i, 'disconnectTime']
        y.loc[start_:end_, 'is_available'] = 0
    return y  # y is a dataframe with a datetime index and two columns, is_available and sessionID

def create_wide_y(df, start_date='2019-03-25', end_date='2021-09-12'):
    tmp = df.copy()
    tmp.set_index('connectionTime', inplace=True)
    tmp = tmp.sort_index().loc[start_date:end_date, :]

    space_cols = tmp.spaceID.unique()
    space_cols = (list(space_cols.astype('str')))

    y = pd.DataFrame(index=pd.date_range(start_date, end_date, inclusive='both', freq='h', tz=0), columns=space_cols)
    y[space_cols] = 1

    tmp.reset_index(inplace=True)

    for i in list(tmp.index):
        start_ = tmp.loc[i, 'connectionTime']
        end_ = tmp.loc[i, 'disconnectTime']
        session_ = tmp.loc[i, 'sessionID']
        space_ = tmp.loc[i, 'spaceID']
        # print(start_,'\t', end_,'\t', session_, '\t', space_)
        try:
            y.loc[start_:end_, space_] = 0
        except:
            print('bad value:')
            print(i, '\t', start_, '\t', end_, '\t', session_, '\t', space_)

    return y

def create_all_site_y(df, regression=True):
    """This function makes a y pd.series for modeling all sites.
    It does this by doing the following process
    1. checks incoming dataframe for correct configuration
    2. creates a list of all unique sites in the df
    3. creates the empty all_y dataframe
    4. loops through each site and
        a. identifies the spaces, start, and end dates of that site
        b. creates an all available y dataframe for that site
        c. for each charging entry
            i. marks the space as occupied for that hour
        d. if the outcome variable is regression, divides number of available spots by the total number of spaces
        e. combines all y's together
    5. returns the y dataframe"""
    assert {'connectionTime', 'disconnectTime', 'siteID', 'spaceID'}.issubset(df.columns)
    sites = list(df.siteID.unique())
    all_y = pd.DataFrame()

    for site in sites:
        # identify spaces, start, and end dates
        space_cols = list(df.loc[df['siteID'] == site, 'spaceID'].unique()) # saves all of the unique spaces as a list of strings
        start_date, end_date = get_start_end_times(df[df['siteID'] == site])
        # start_date = df.loc[df['siteID'] == site, 'connectionTime'].min().date() # gets min connection date
        # end_date = df.loc[df['siteID'] == site, 'disconnectTime'].max().date() + pd.Timedelta('1d') # gets one day after last disconnect date

        # create y frame
        y = pd.DataFrame(index=pd.date_range(start_date, end_date, inclusive='both', freq='h', tz=0), columns=space_cols)
        y[space_cols] = 1

        # prepare loop
        tmp = df[df['siteID'] == site].reset_index()

        for i in list(tmp.index):
            start_ = tmp.loc[i, 'connectionTime']
            end_ = tmp.loc[i, 'disconnectTime']
            space_ = tmp.loc[i, 'spaceID']
            try:
                y.loc[start_:end_, space_] = 0
            except:
                print('bad value:')
                print(i, '\t', start_, '\t', end_, '\t', space_)

        if regression:
            y = y.sum(axis=1)/len(space_cols)

        # combine y's from different sites
        if all_y.empty:
            all_y = y
        else:
            all_y = pd.concat([all_y, y], axis=0)
    return all_y






def create_x(start, end, caiso_fp=None, sun_fp=None):
    x = pd.DataFrame(index=pd.date_range(start, end, inclusive='both', freq='h', tz=0),
                     columns=['dow', 'hour', 'month', 'is_sunny'])
    x['dow'] = x.index.dayofweek
    x['hour'] = x.index.hour
    x['month'] = x.index.month
    x['is_sunny'] = 0

    x = holiday_processing(x)

    if caiso_fp:
        caiso = pd.read_csv(caiso_fp)
        caiso['datetime'] = pd.to_datetime(caiso['date'] + ' ' + caiso['Time'], errors='coerce', utc=True)
        caiso = caiso.set_index('datetime')
        caiso.drop(columns=['date', 'Time'], inplace=True)
        caiso_hourly = caiso.groupby(pd.Grouper(freq='1h')).mean()
        caiso_hourly.index.tz_localize(None)
        drop_cols = ['Net demand forecast', 'Natural Gas', 'Large Hydro', 'Demand', 'Net Demand',
                     'Day-ahead demand forecast',
                     'Day-ahead net demand forecast', 'Resource adequacy capacity forecast',
                     'Net resource adequacy capacity forecast',
                     'Reserve requirement', 'Reserve requirement forecast', 'Resource adequacy credits']
        for i in caiso_hourly.columns:
            caiso_hourly[i] = caiso_hourly[i].interpolate(method='time')
        x = x.join(caiso_hourly.drop(columns=drop_cols))

    if sun_fp:
        sun = pd.read_csv(sun_fp)
        sun['sunrise_ts'] = pd.to_datetime(sun['date'] + ' ' + sun['sunrise'], errors='coerce', utc=True)
        sun['sunset_ts'] = pd.to_datetime(sun['date'] + ' ' + sun['sunset'], errors='coerce', utc=True)
        for i in list(sun.index):
            start_ = sun.loc[i, 'sunrise_ts']
            end_ = sun.loc[i, 'sunset_ts']
            x.loc[start_:end_, 'is_sunny'] = 1
    else:
        x = x.drop(columns='is_sunny')

    return x

def update_varuns_x(X, site_id):
    X['siteID'] = site_id
    return X

def get_start_end_times(df):
    """returns the start and end time of the site dataframe
    which equates to midnight of the first connectionTime date and
    one day after the max disconnectTime date"""
    start_date = df.loc[:, 'connectionTime'].min().date()
    end_date = df.loc[:, 'disconnectTime'].max().date() + pd.Timedelta('1d')
    return start_date, end_date

# TODO: Deprecate
def create_all_site_x(df):
    assert {'connectionTime', 'disconnectTime', 'siteID'}.issubset(df.columns)
    sites = list(df.siteID.unique())
    all_X = pd.DataFrame()
    for site in sites:
        start_date = df.loc[df['siteID'] == site, 'connectionTime'].min().date()
        end_date = df.loc[df['siteID'] == site, 'disconnectTime'].max().date() + pd.Timedelta('1d')

        X = pd.DataFrame(index=pd.date_range(start_date, end_date, inclusive='both', freq='h', tz=0),
                         columns=['dow', 'hour', 'month', 'siteID'])
        X['dow'] = X.index.dayofweek
        X['hour'] = X.index.hour
        X['month'] = X.index.month
        X['connectionTime'] = X.index
        X['siteID'] = site
        X = holiday_processing(X).drop(columns=['connectionTime'])

        if all_X.empty:
            all_X = X
        else:
            all_X = pd.concat([all_X, X], axis=0)
    return all_X

