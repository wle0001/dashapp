#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 23 16:48:06 2022

@author: ellenbw
"""

import pandas as pd


def vmc(x):

    mc = (4.824e-10*(x**3))-(2.278e-6*(x**2))+(3.898e-3*x)-2.154
    
    return mc

urlDict = {'STEMNet1':'https://emeshnetwork.net/stemmnet-upload/devices/33459-1486836.csv',
           'STEMNet2':'https://emeshnetwork.net/stemmnet-upload/devices/68009-1616323.csv'}


stm_df = pd.DataFrame()
for url in urlDict: 

    a = pd.read_csv(urlDict[url])
    
    
    columns = ['SOIL_MOISTURE_5_DAILY','SOIL_MOISTURE_20_DAILY',
               'SOIL_MOISTURE_50_DAILY']
    
    a[columns] = a['moistures'].str.split(';', expand = True)
    a[columns] = a[columns].apply(pd.to_numeric)
    a[columns] = a[columns].apply(vmc)
    
    a['site'] = url
    
    a.index = pd.to_datetime(a['datetime'], unit = 's')
    
    a = a.resample('D').mean()
    
    a['LST_DATE'] = a.index
    
    a['site'] = url
    
    stm_df = stm_df.append(a)





stm_df.to_csv('STEMNet_AL_all.csv')




SCAN = pd.read_csv('SCAN_AL_SMS_only.csv')
#print('SCAN')
#print(SCAN.shape)
#print(SCAN.columns)

scan = SCAN[['Date', 'station','SMS-2.0in', 'SMS-4.0in', 'SMS-8.0in', 'SMS-20.0in','SMS-40.0in']].copy()
scan['Date'] = pd.to_datetime(scan['Date'],format='%Y-%m-%d')
scan.columns = ['Date', 'station','5cm','10cm','20cm','50cm', '100cm']
scan['station_type'] = 'SCAN'
scan_stations = list(scan['station'].unique())
# ---------- CRN DATA ----------------------
CRN = pd.read_csv('CRN_AL_all.csv')
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



STM = pd.read_csv('STEMNet_AL_all.csv')
STM2 = STM.replace(to_replace=-99.0, value=np.nan)
#print('CRN')
stm = STM2[['site', 'LST_DATE',
           'SOIL_MOISTURE_5_DAILY','SOIL_MOISTURE_20_DAILY',
           'SOIL_MOISTURE_50_DAILY']].copy()
stm.columns = ['station','Date','5cm','10cm','20cm']
stm['station_type'] = 'STMNet'
stm['Date'] = pd.to_datetime(stm['Date'],format='%Y-%m-%d')
#print(crn.shape)
#print(crn.columns)
stm_stations = list(stm['station'].unique())


scan_real_min = scan.dropna(how='all', subset=['5cm', '10cm', '20cm', '50cm', '100cm'])
min_scan_dates = scan.groupby('station')['Date'].min().reset_index(name='min_date')

crn_real_min = crn.dropna(how='all', subset=['5cm', '10cm', '20cm', '50cm', '100cm'])
min_crn_dates = crn_real_min.groupby('station')['Date'].min().reset_index(name='min_date')


stm_real_min = stm.dropna(how='all', subset=['5cm', '10cm', '20cm'])
min_stm_dates = stm_real_min.groupby('station')['Date'].min().reset_index(name='min_date')

depth_start_dates = min_scan_dates.append(min_crn_dates).append(min_stm_dates)

# get list of all possible stations. Need this to make the master_df below:
stations = depth_start_dates['station'].values.tolist()

big_df = scan_real_min.append(crn_real_min).append(stm_real_min)
#print(big_df.shape)


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
    df['surface_7d_mean'] = (df['5cm_7d'] + df['10cm_7d']) / 2
    df['root_7d_mean'] = (df['20cm_7d'] + df['50cm_7d'] + df['100cm_7d']) / 3

    master_df = master_df.append(df)





