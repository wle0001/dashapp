#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 11:39:51 2022

@author: ellenbw
"""

import pandas as pd
import numpy as np

stns = pd.read_csv('ET_data_EPA/stations.csv')['STATION_ID']

for stn in stns:

    df = pd.DataFrame()
    for yr in np.arange(2009,2021):
        
        a = pd.read_csv('https://www.ncei.noaa.gov/data/global-hourly/access/{}/{}.csv'.format(yr, stn))
        
        df = pd.concat([df,a])
    df.to_csv('ET_data_EPA/{}_09-20.csv'.format(stn))
    sys.exit()

        
        
        
    