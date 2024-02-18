import pandas as pd

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
    df['connectionTime'] = pd.to_datetime(df['connectionTime'], infer_datetime_format=True, utc=True, errors='coerce')
    df['connectionTimeHour'] = df['connectionTime'].dt.hour
    df['connectionTimeDay'] = df['connectionTime'].dt.day
    df['disconnectTime'] = pd.to_datetime(df['disconnectTime'], infer_datetime_format=True, utc=True, errors='coerce')
    df['disconnectTimeHour'] = df['disconnectTime'].dt.hour
    df['disconnectTimeDay'] = df['disconnectTime'].dt.day
    df['doneChargingTime'] = pd.to_datetime(df['doneChargingTime'], infer_datetime_format=True, utc=True, errors='coerce')
    df['doneChargingTimeHour'] = df['doneChargingTime'].dt.hour
    df['doneChargingTimeDay'] = df['doneChargingTime'].dt.day
    return df