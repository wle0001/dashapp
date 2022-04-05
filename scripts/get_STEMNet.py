#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 23 16:48:06 2022

@author: ellenbw
"""

import pandas as pd
import numpy as np


def vmc(x):

    mc = (4.824e-10*(x**3))-(2.278e-6*(x**2))+(3.898e-3*x)-2.154
    
    mc = mc*100
    
    return mc

urlDict = {'STEMNet-1':'https://emeshnetwork.net/stemmnet-upload/devices/33459-1486836.csv',
           'STEMNet-2':'https://emeshnetwork.net/stemmnet-upload/devices/68009-1616323.csv',
           'STEMNet-3':'https://emeshnetwork.net/stemmnet-upload/devices/35199-185355.csv'}


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

