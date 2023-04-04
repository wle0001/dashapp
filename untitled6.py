#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 16:43:28 2022

@author: ellenbw
"""

import pandas as pd
from datetime import date, timedelta
import numpy as np

# ---------- SCAN DATA -----------------------
scan_path = 'scripts/'
SCAN = pd.read_csv(scan_path + 'SCAN_AL_SMS_only.csv')
#print('SCAN')
#print(SCAN.shape)
#print(SCAN.columns)

scan = SCAN[['Date', 'station','SMS-2.0in', 'SMS-4.0in', 'SMS-8.0in', 'SMS-20.0in','SMS-40.0in']].copy()
scan['Date'] = pd.to_datetime(scan['Date'],format='%Y-%m-%d')
scan.columns = ['Date', 'station','5cm','10cm','20cm','50cm', '100cm']
scan['station_type'] = 'SCAN'
scan_stations = list(scan['station'].unique())
# ---------- CRN DATA ----------------------
CRN = pd.read_csv(scan_path + 'CRN_AL_all.csv')
CRN2 = CRN.replace(to_replace=-99.0, value=np.nan)
#print('CRN')
crn = CRN2[['site', 'LST_DATE',
           'SOIL_MOISTURE_5_DAILY','SOIL_MOISTURE_10_DAILY',
           'SOIL_MOISTURE_20_DAILY','SOIL_MOISTURE_50_DAILY',
           'SOIL_MOISTURE_100_DAILY']].copy()
crn.columns = ['station','Date','5cm','10cm','20cm','50cm', '100cm']
crn['station_type'] = 'CRN'
crn['Date'] = pd.to_datetime(crn['Date'],format='%Y-%m-%d')
#print(crn.shape)
#print(crn.columns)
crn_stations = list(crn['station'].unique())

# ---------- STEMNet DATA ----------------------
STM = pd.read_csv(scan_path + 'STEMNet_AL_all.csv')
STM2 = STM.replace(to_replace=-99.0, value=np.nan)
#print('CRN')
stm = STM2[['site', 'LST_DATE',
           'SOIL_MOISTURE_5_DAILY','SOIL_MOISTURE_20_DAILY',
           'SOIL_MOISTURE_50_DAILY']].copy()
stm.columns = ['station','Date','5cm','20cm','50cm']
stm['station_type'] = 'STMNet'
stm['Date'] = pd.to_datetime(stm['Date'],format='%Y-%m-%d')
#print(crn.shape)
#print(crn.columns)
stm_stations = list(stm['station'].unique())

# ----------- METADATA ---------
#compare = pd.read_csv(scan_path + 'CRN_SCAN_soil_meta_mini.csv')
compare = pd.read_csv(scan_path + 'soil_meta_mini.csv')#added STEMNet
mid_lon = (compare['longitude'].max() + compare['longitude'].min())/2
#print(mid_lon) # -86.7
mid_lat = (compare['latitude'].max() + compare['latitude'].min())/2
#print(mid_lat) #32.7

# --------- GETTING THE 7-DAY AVERAGES OVERALL TABLE ---------------------
# subset to get just needed columns then get min date for soil moisture data for each station
scan_real_min = scan.dropna(how='all', subset=['5cm', '10cm', '20cm', '50cm', '100cm'])
min_scan_dates = scan.groupby('station')['Date'].min().reset_index(name='min_date')

crn_real_min = crn.dropna(how='all', subset=['5cm', '10cm', '20cm', '50cm', '100cm'])
min_crn_dates = crn_real_min.groupby('station')['Date'].min().reset_index(name='min_date')

stm_real_min = stm.dropna(how='all', subset=['5cm', '20cm', '50cm'])
min_stm_dates = stm_real_min.groupby('station')['Date'].min().reset_index(name='min_date')

# put the scan and crn start dates together as one df: depth_start_dates
depth_start_dates = min_scan_dates.append(min_crn_dates).append(min_stm_dates)

# get list of all possible stations. Need this to make the master_df below:
stations = depth_start_dates['station'].values.tolist()

big_df = scan_real_min.append(crn_real_min).append(stm_real_min)
#print(big_df.shape)

depth_start_dates.set_index('station', inplace=True)
#print(depth_start_dates.head())
end = big_df['Date'].max()

# Making a df where we have all 7-day rolling averages for each station
master_df = pd.DataFrame()
for stn in stations:
    df1 = big_df[big_df['station']==stn]
    # get list of all possible dates from earliest collection to latest
    start = depth_start_dates.loc[stn,'min_date']
    dates = list(pd.date_range(start, end))
    # start new df with DATES column
    df_dates = pd.DataFrame(dates, columns=['DATES'])
    df = pd.merge(df_dates, df1, left_on='DATES', right_on='Date', how='left')
    #print(df1.shape)
    #print(df.shape)

    # Get rolling 7-day averages (no center=True or .shift()) - Ask to be sure
    # need at least 4 values to get 7-day avg
    df['5cm_7d'] = df['5cm'].rolling(window=7,min_periods=4).mean()
    df['10cm_7d'] = df['10cm'].rolling(window=7, min_periods=4).mean()
    df['20cm_7d'] = df['20cm'].rolling(window=7, min_periods=4).mean()
    df['50cm_7d'] = df['50cm'].rolling(window=7, min_periods=4).mean()
    df['100cm_7d'] = df['100cm'].rolling(window=7, min_periods=4).mean()
    # Get surface and root-zone means
    if stn[:4] == 'STEM':
        df['surface_7d_mean'] = df['5cm_7d']
        df['root_7d_mean'] = (df['20cm_7d'] + df['50cm_7d']) / 2
    else:
        df['surface_7d_mean'] = (df['5cm_7d'] + df['10cm_7d']) / 2
        df['root_7d_mean'] = (df['20cm_7d'] + df['50cm_7d'] + df['100cm_7d']) / 3

    #df['surface_7d_mean'] = (df['5cm_7d'] + df['10cm_7d']) / 2
    #df['root_7d_mean'] = (df['20cm_7d'] + df['50cm_7d'] + df['100cm_7d']) / 3

    master_df = master_df.append(df)

master_df['mo_day'] = master_df['Date'].dt.strftime('%m-%d')

pct_df = master_df.groupby(['station','mo_day'])['surface_7d_mean'].describe(percentiles=[0.05, 0.1, 0.25, 0.75, 0.8, 0.95]).reset_index()
pct_df.columns = ['station', 'mo_day', 'count_7d', 'mean_s', 'std_s', 'min_s', '5%_s', '10%_s', '25%_s',
       '50%_s', '75%_s', '80%_s', '95%_s', 'max_s']

big_df = pd.merge(master_df,pct_df,on=['station','mo_day'])

pct_df = master_df.groupby(['station','mo_day'])['root_7d_mean'].describe(percentiles=[0.05, 0.1, 0.25, 0.75, 0.8, 0.95]).reset_index()

pct_df.columns = ['station', 'mo_day', 'count_7d', 'mean_r', 'std_r', 'min_r', '5%_r', '10%_r', '25%_r',
       '50%_r', '75%_r', '80%_r', '95%_r', 'max_r']

big_df = pd.merge(big_df,pct_df,on=['station','mo_day'])

big_df.to_csv('updatedSCANdata.csv')



