import datetime

import numpy as np
import pandas as pd
import os
import sqlalchemy

from mysecrets import hostname, username, password
import psycopg2

def get_connection():
 return psycopg2.connect(
  host=hostname,
  database="postgres",
  user=username,
  password=password)


from sqlalchemy import create_engine, MetaData, Column, Integer, String, Table, Numeric, DateTime, Date, Boolean, BigInteger, Time
from sqlalchemy.sql import func

connection_string = f'postgresql://{username}:{password}@{hostname}:5432/postgres'
# conn = get_connection()
conn = create_engine(connection_string)
print(conn)


# location_data.to_sql('d_locations', conn, if_exists='append', index=False)
def populate_d_locations(conn):

    print('populating d_locations')
    locations = [['caltech', 'California_Garage_01', 'CA'],
              ['caltech', 'California_Garage_02', 'CA'],
              ['caltech', 'LIGO_01', 'CA'],
              ['caltech', 'N_Wilson_Garage_01', 'CA'],
              ['caltech', 'S_Wilson_Garage_01', 'CA'],
              ['jpl', 'Arroyo_Garage_01', 'CA'],
              ['office_01', 'Parking_Lot_01', 'CA'],
              ]
    location_data = pd.DataFrame(locations, columns=['major_name', 'minor_name', 'state'])
    location_data.to_sql('d_locations', conn, if_exists='append', index=False)
    return 1

def create_table_d_locations(conn):
    metadata = MetaData()  # stores the 'production' database's metadata

    locations_table = Table('d_locations', metadata,
                            Column('id', Integer, primary_key=True, autoincrement=True),
                            Column('major_name', String),
                            Column('minor_name', String),
                            Column('state',
                                   String))  # defines the 'users' table structure in the 'python' schema of our connection to the 'production' db

    try:
        locations_table.drop(conn)  # drops the d_locations table
        print('droped old d_locations table')
    except:
        print('making new d_locations table')
    locations_table.create(conn)  # creates the users table

    return 1

def make_d_locations():
    connection_string = f'postgresql://{username}:{password}@{hostname}:5432/postgres'
    conn = create_engine(connection_string)

    create_table_d_locations(conn)
    populate_d_locations(conn)
    pass

# make_d_locations()
def create_table_d_files(conn):

    metadata = MetaData()
    files_table = Table('d_files', metadata,
                          Column('id', Integer, primary_key=True),
                          Column('full_path', String),
                          Column('filename', String))
    try:
        files_table.drop(conn)  # drops the d_locations table
        print('droped old files_table table')
    except:
        print('making new files_table table')
    files_table.create(conn)  # creates the files_table table

    return 1
def create_table_d_dates(conn):


    metadata = MetaData()
    dates_table = Table('d_dates', metadata,
                          Column('date', Date, primary_key=True),
                          Column('is_holiday', Boolean),
                          Column('dow', Integer))
    try:
        dates_table.drop(conn)  # drops the d_locations table
        print('droped old dates_table table')
    except:
        print('making new dates_table table')
    dates_table.create(conn)  # creates the users table
    return 1

def create_table_f_charges(conn):
    metadata = MetaData()  # stores the 'production' database's metadata

    charges_table = Table('f_charges', metadata,
                            Column('id', BigInteger, primary_key=True, autoincrement=True),
                            Column('datetime', DateTime, nullable=False),
                            Column('location_id', Integer, nullable=False),
                          Column('file_id', Integer, nullable=False),
                          Column('charging_current_amps', Numeric, nullable=True),
                          Column('actual_pilot_amps', Numeric, nullable=True),
                          Column('voltage_volts', Numeric, nullable=True),
                          Column('charging_state', String, nullable=True),
                          Column('energy_delivered_kwh', Numeric, nullable=True),
                          Column('power_kw', Numeric, nullable=True),
                          Column('date', Date),
                          Column('time', Time),
                          Column('created_on', DateTime, nullable=False, server_default=func.now()),
                          Column('updated_on', DateTime, nullable=True, onupdate=func.now()),

                          )
    try:
        charges_table.drop(conn)  # drops the d_locations table
        print('droped old charges table')
    except:
        print('making new f_charges table')
    charges_table.create(conn)  # creates the users table
    return 1

def main():
    make_d_locations()
    conn = get_connection()
    connection_string = f'postgresql://{username}:{password}@{hostname}:5432/postgres'
    # conn = get_connection()
    conn = create_engine(connection_string)
    create_table_d_dates(conn)
    create_table_f_charges(conn)
    create_table_d_files(conn)


main()



