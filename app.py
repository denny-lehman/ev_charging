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


st.title('Charge Buddy: Charger Availability')
st.sidebar.title("Options")
st.sidebar.subheader('Select location')
location = st.sidebar.selectbox('Click below to select a new asset',
                                 ['Office001','Caltech','JPL'], index=0,
                                 # format_func=label
                     )
start_date = st.sidebar.date_input("Start date", value=datetime.date(2021,1,4))
end_date = st.sidebar.date_input("End date", value=datetime.date(2021,1,6))
st.sidebar.button("Run")


# st.sidebar.info('EDIT ME: This app is a simple example of '
#                 'using Strealit to create a financial data web app.\n'
#                 '\nIt is maintained by [Paduel]('
#                 'https://twitter.com/paduel_py).\n\n'
#                 'Check the code at https://github.com/paduel/streamlit_finance_chart')

data_load_state = st.text('Loading data...')
df = load_data()
data_load_state.text('Loading data...done!')



model_load_state = st.text('Loading model...')
clf = load_model()
model_load_state.text('Loading model...done!')
st.write(clf)

y = create_wide_y(df)
y = y.sum(axis=1)

st.subheader(f'How often are spots available at {location}')
hist_values = np.histogram(y, bins=9, range=(0,9))[0]
st.bar_chart(hist_values)

st.subheader('Availability')
model = pickle.load(open('../model.pkl', 'rb'))
model = load_model()
st.write(start_date, end_date)
# start_date = '2021-01-04'
# end_date = '2021-01-06'
X = create_x(df, start_date=start_date, end_date=end_date)
prediction = pd.Series(model.predict(X), index=X.index)
st.bar_chart(prediction)
