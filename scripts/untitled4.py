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

wsdl = 'https://wcc.sc.egov.usda.gov/awdbWebService/services?WSDL'
# Intialize the client
#https://www.nrcs.usda.gov/wps/portal/wcc/home/dataAccessHelp/webService/webServiceReference/
client = Client(wsdl, transport=Transport(session=session))

start_date = date(2000,1,1).strftime('%Y-%m-%d')
end_date = date(2022, 5, 12).strftime('%Y-%m-%d')

param = 'SMS'

stn = '2180:AL:SCAN'

depth = -2.0


retval = client.service.getData(stationTriplets=stn, elementCd=param, ordinal=1,
                                                duration='DAILY', getFlags=False, beginDate=start_date,
                                                alwaysReturnDailyFeb29=False, endDate=end_date,
                                                heightDepth={'unitCd': 'in', 'value': depth})
'''

retval = client.service.getHourlyData(stationTriplets=stn, elementCd=param, ordinal=1,
                                                beginDate=start_date,
                                                endDate=end_date,
                                                heightDepth={'unitCd': 'in', 'value': depth})
'''

temp_df = pd.DataFrame()
temp_df['Date'] = pd.date_range(start=retval[0].beginDate, end=retval[0].endDate, freq='D')
result = [val for val in retval[0].values]
# here, I make the list items a float value, or NaN (for easier downstream data analyses)
result2 = []
for x in result:
    try:
        result2.append(float(x))
    except:
        result2.append(np.nan)
# creating column name with depth and "in" for inches
col_name = str(str(param) + str(depth) + 'in')
# append the data to the new column
temp_df[col_name] = result2

temp_df.index = temp_df['Date']
temp_df = temp_df.drop('Date', axis = 1)
# merge to the sm_df (which has the station column)
# in other words, merge the data column with the correct station column
#sm_df = pd.merge(sm_df, temp_df, on='Date', how='outer')



def vmc(x):

    mc = (4.824e-10*(x**3))-(2.278e-6*(x**2))+(3.898e-3*x)-2.154
    
    mc = mc*100
    
    return mc

def vmc2(x):

    mc = (-0.0207*(x**3))+(1.9062*(x**2))+(54.998*x)+2390
    
    #mc = mc*100
    
    return mc

urlDict = {'STEMNet-2':'https://emeshnetwork.net/stemmnet-upload/devices/33459-1486836.csv',
           'STEMNet-1':'https://emeshnetwork.net/stemmnet-upload/devices/68009-1616323.csv'}
stm_df = pd.DataFrame()
for url in urlDict: 

    a = pd.read_csv(urlDict[url])
    
    
    columns = ['SOIL_MOISTURE_5_DAILY','SOIL_MOISTURE_20_DAILY',
               'SOIL_MOISTURE_50_DAILY']
    
    a[columns] = a['moistures'].str.split(';', expand = True)
    a[columns] = a[columns].apply(pd.to_numeric)
    #poly = np.array([-9.27756773e-05,  5.28244528e-01, -1.00226268e+03,  6.33718261e+05])
    #a[columns] = np.polyval(poly,a[columns])
    #a[columns] = a[columns].apply(vmc)
    
    a['site'] = url
    
    a.index = pd.to_datetime(a['datetime'], unit = 's', utc = True)
    a.index = a.index.tz_convert(cen)
    
    a = a.resample('H').mean()
    
    a['LST_DATE'] = a.index
    
    a['site'] = url
    
    stm_df = stm_df.append(a)


stm_r = stm_df[stm_df['site'] == 'STEMNet-1']


stm_r['SOIL_MOISTURE_20_DAILY'].plot()
temp_df['SMS-8.0in'].plot()
'''
poly = np.array([-9.27756773e-05,  5.28244528e-01, -1.00226268e+03,  6.33718261e+05])
x1 = np.polyval(poly,stm_r['SOIL_MOISTURE_5_DAILY'][-960:].resample('D').mean())
y1 = temp_df['SMS-2.0in'][-960:].resample('D').mean().values
plt.scatter(x1, y1)
'''
ax = stm_r['SOIL_MOISTURE_20_DAILY'].plot()
ax1 = ax.twinx()
temp_df['SMS-8.0in'].plot(ax = ax1, color = 'orange')
'''
x = temp_df['SMS-8.0in'].resample('D').mean()[-100:].values
y = stm_r['SOIL_MOISTURE_20_DAILY'].resample('D').mean()[-100:].values
z = temp_df['SMS-8.0in'][-100:].resample('D').mean().index.strftime('%j').values.astype(int)

annotations=z

plt.scatter(x,y,c=z,cmap='viridis')
plt.colorbar()
for i, label in enumerate(annotations):
    plt.annotate(label, (x[i], y[i]))
    
plt.colorbar()
'''

x = np.arange(1870,1940,1)
poly = np.array([-9.27756773e-05,  5.28244528e-01, -1.00226268e+03,  6.33718261e+05])
poly = np.array([ 1.14663149e-04, -6.62265520e-01,  1.27500130e+03, -8.18165925e+05])
a = np.polyval(poly,x)
#a = vmc(x)
#a = 0.199*x-344.7
#a = vmc(x)
plt.plot(x, a)



#plt.legend()

'''
fname = 'soil_aamu1_11cm'
t = pd.read_csv('../../../soilmoisture /soilLab/feb9/{}.csv'.format(fname), 
                header =None, names = ['SOIL_MOISTURE_5_DAILY','SOIL_MOISTURE_20_DAILY',
               'SOIL_MOISTURE_50_DAILY'])
              

t = t.apply(pd.to_numeric)
t = t.apply(vmc)

t.plot()
'''


x = temp_df['SMS-8.0in'].resample('D').mean()[-100:].values
y = stm_r['SOIL_MOISTURE_20_DAILY'].resample('D').mean()[-100:].values
z = temp_df['SMS-8.0in'][-100:].resample('D').mean().index.strftime('%j').values.astype(int)

a = pd.DataFrame([x,y]).T
a.columns = ['scan','stem']

a['stem-sm'] = 0.199*a['stem']-344.7
#a['stem-sm'] = np.polyval(poly,a['stem'])
a.index = temp_df['SMS-8.0in'].resample('D').mean()[-100:].index
a[['scan','stem-sm']].plot()




