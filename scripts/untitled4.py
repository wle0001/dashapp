#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 26 18:25:20 2022

@author: ellenbw
"""

import pandas as pd
from zeep import Client
from zeep.transports import Transport
from requests import Session
import urllib3
from datetime import date, timedelta, datetime
import numpy as np
import sys
import matplotlib.pyplot as plt

import pytz

cen = pytz.timezone('US/Central')
utc = pytz.utc
#fmt = '%Y-%m-%d %H:%M:%S %Z%z'

urllib3.disable_warnings()

session = Session()
session.verify = False

wsdl = 'https://www.wcc.nrcs.usda.gov/awdbWebService/services?WSDL'
# Intialize the client
client = Client(wsdl, transport=Transport(session=session))

start_date = date(2022,2,15).strftime('%Y-%m-%d')
end_date = date(2022, 3, 2).strftime('%Y-%m-%d')

param = 'SMS'

stn = '2078:AL:SCAN'

depth = -20.0

'''
retval = client.service.getData(stationTriplets=stn, elementCd=param, ordinal=1,
                                                duration='HOURLY', getFlags=False, beginDate=start_date,
                                                alwaysReturnDailyFeb29=False, endDate=end_date,
                                                heightDepth={'unitCd': 'in', 'value': depth})
'''

retval = client.service.getHourlyData(stationTriplets=stn, elementCd=param, ordinal=1,
                                                beginDate=start_date,
                                                endDate=end_date,
                                                heightDepth={'unitCd': 'in', 'value': depth})


temp_df = pd.DataFrame()
temp_df['Date'] = pd.date_range(start=retval[0].beginDate, end=retval[0].endDate, freq='H')
result = [val for val in retval[0].values]
# here, I make the list items a float value, or NaN (for easier downstream data analyses)
result2 = []
for x in result:
    try:
        result2.append(float(x['value']))
    except:
        result2.append(np.nan)
# creating column name with depth and "in" for inches
col_name = str(str(param) + str(depth) + 'in')
# append the data to the new column
temp_df[col_name] = result2

temp_df.index = temp_df['Date']
# merge to the sm_df (which has the station column)
# in other words, merge the data column with the correct station column
#sm_df = pd.merge(sm_df, temp_df, on='Date', how='outer')



def vmc(x):

    mc = (4.824e-10*(x**3))-(2.278e-6*(x**2))+(3.898e-3*x)-2.154
    
    mc = mc*100
    
    return mc

urlDict = {'STEMNet-1':'https://emeshnetwork.net/stemmnet-upload/devices/33459-1486836.csv',
           'STEMNet-2':'https://emeshnetwork.net/stemmnet-upload/devices/68009-1616323.csv'}
stm_df = pd.DataFrame()
for url in urlDict: 

    a = pd.read_csv(urlDict[url])
    
    
    columns = ['SOIL_MOISTURE_5_DAILY','SOIL_MOISTURE_20_DAILY',
               'SOIL_MOISTURE_50_DAILY']
    
    a[columns] = a['moistures'].str.split(';', expand = True)
    a[columns] = a[columns].apply(pd.to_numeric)
    #a[columns] = a[columns].apply(vmc)
    
    a['site'] = url
    
    a.index = pd.to_datetime(a['datetime'], unit = 's', utc = True)
    a.index = a.index.tz_convert(cen)
    
    a = a.resample('H').mean()
    
    a['LST_DATE'] = a.index
    
    a['site'] = url
    
    stm_df = stm_df.append(a)


stm_r = stm_df[stm_df['site'] == 'STEMNet-1']


stm_r['SOIL_MOISTURE_50_DAILY'].plot()
temp_df['SMS-20.0in'].plot()

ax = stm_r['SOIL_MOISTURE_50_DAILY'].plot()
ax1 = ax.twinx()
temp_df['SMS-20.0in'].plot(ax = ax1, color = 'orange')
'''
x = temp_df['SMS-20.0in'][-240:].values
y = stm_r['SOIL_MOISTURE_50_DAILY'][-240:].values
z = temp_df['SMS-20.0in'][-240:].index.strftime('%j').values.astype(int)

annotations=z

plt.scatter(x,y,c=z,cmap='viridis')
plt.colorbar()
for i, label in enumerate(annotations):
    plt.annotate(label, (x[i], y[i]))
    
plt.colorbar()
'''



plt.legend()

'''
fname = 'soil_aamu1_11cm'
t = pd.read_csv('../../../soilmoisture /soilLab/feb9/{}.csv'.format(fname), 
                header =None, names = ['SOIL_MOISTURE_5_DAILY','SOIL_MOISTURE_20_DAILY',
               'SOIL_MOISTURE_50_DAILY'])
              

t = t.apply(pd.to_numeric)
t = t.apply(vmc)

t.plot()
'''




