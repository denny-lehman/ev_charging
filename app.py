import streamlit as st
import pandas as pd
import numpy as np
import datetime
import pickle
import logging

from src.data_preprocessing import datetime_processing, userinput_processing, holiday_processing, create_x, create_wide_y

@st.cache_data
def load_data():
    df_of = pd.read_parquet('data/ACN-API/office001/').reset_index(drop=True)
    df_of = datetime_processing(df_of)
    df_of = userinput_processing(df_of)
    df_of = holiday_processing(df_of)
    return df_of
# @st.cache_data
def load_model():

    model = pickle.load(open('../model.pkl', 'rb'))
    return model

sites = ['Office001','Caltech','JPL']
site_ids = [2,1,19]
site2id = { k:v for (k,v) in zip(sites, site_ids)}

st.title('Charge Buddy')
st.subheader('Helping EV owners know when to charge')
st.sidebar.title("When and where?")
st.sidebar.subheader('Select charging site')
site = st.sidebar.selectbox('Click below to select a charger location',
                                 sites, index=0,
                                 # format_func=label
                     )
st.sidebar.subheader('Select date')
start_date = st.sidebar.date_input("Start date", value=datetime.datetime.today().date())
end_date = st.sidebar.date_input("End date", value=datetime.datetime.today().date() + pd.Timedelta('1d'))
st.sidebar.button("Run")


# st.sidebar.info('EDIT ME: This app is a simple example of '
#                 'using Strealit to create a financial data web app.\n'
#                 '\nIt is maintained by [Paduel]('
#                 'https://twitter.com/paduel_py).\n\n'
#                 'Check the code at https://github.com/paduel/streamlit_finance_chart')






st.subheader('Availability')
model = pickle.load(open('../reg_model.pkl', 'rb'))

st.write(start_date, end_date)
# start_date = '2021-01-04'
# end_date = '2021-01-06'
# X = create_x(start=start_date, end=end_date)

X = pd.DataFrame(index=pd.date_range(start_date, end_date, inclusive='both', freq='h', tz=0),
                     columns=['dow', 'hour', 'month', 'siteID'])
# X['dow'] = X.index.dt.hour
X['dow'] = X.index.dayofweek
X['hour'] = X.index.hour
X['month'] = X.index.month
X['connectionTime'] = X.index
X = holiday_processing(X).drop(columns=['connectionTime'])
X['siteID'] = site2id[site]
prediction = pd.Series(model.predict(X), index=X.index, name='% available')

# regression messes up sometimes
prediction[prediction>1] = 1
prediction[prediction<0] = 0

st.bar_chart(prediction, y='% available')


st.subheader(f'How often are spots available at {site}')
# st.text(f'Very available. Average number of open charger spots {np.round(y.mean(),1)} out of {y.max()}')
st.text('More locations coming soon... ')

# hist_values = np.histogram(y, bins=9, range=(0,9))[0]
# st.bar_chart(hist_values)