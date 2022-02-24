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

#a = pd.read_csv('https://emeshnetwork.net/stemmnet-upload/devices/33459-1486836.csv')
a = pd.read_csv('https://emeshnetwork.net/stemmnet-upload/devices/68009-1616323.csv')

a[['SM_2', 'SM_8', 'SM_20']] = a['moistures'].str.split(';', expand = True)
a[['SM_2', 'SM_8', 'SM_20']] = a[['SM_2', 'SM_8', 'SM_20']].apply(pd.to_numeric)
a[['SM_2', 'SM_8', 'SM_20']] = a[['SM_2', 'SM_8', 'SM_20']].apply(vmc)


a.index = pd.to_datetime(a['datetime'], unit = 's')

a.head()






