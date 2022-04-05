"""
Description: Get SCAN (Soil Climate Analysis Network) soil moisture data.
Data is from the air-water database (AWDB) of the USDA Natural Resources Conservation Service (NRCS):
https://www.wcc.nrcs.usda.gov/web_service/AWDB_Web_Service_Reference.htm#getdata
SCAN is a pilot project of NRCS started in 1991 and focuses on agricultural areas of the U.S.
(https://www.drought.gov/data-maps-tools/soil-climate-analysis-network-scan)

Summary:
    Update the SMS data with all 5 soil depths. Script checks the last date in the input file and then add all current date from that date to today's date
Input:
    SCAN_AL_SMS_only.csv
        make sure this is in the same directory as this script!
Output:
    SCAN_AL_SMS_only.csv
        new info gets added to the df

"""

import pandas as pd
from zeep import Client
from zeep.transports import Transport
from requests import Session
import urllib3
from datetime import date, timedelta, datetime
import numpy as np
import sys

# Disable warnings. Not sure this is needed.
urllib3.disable_warnings()

session = Session()
session.verify = False

# https://www.wcc.nrcs.usda.gov/web_service/AWDB_Web_Service_Reference.htm#getdata
# URL to access AWDB webservices
wsdl = 'https://wcc.sc.egov.usda.gov/awdbWebService/services?WSDL'

# Intialize the client
client = Client(wsdl, transport=Transport(session=session))
# Following command can be used to check if the webservice is active
#print(client.service.areYouThere())

scan_path = ''
SCAN = pd.read_csv(scan_path + 'SCAN_AL_SMS_only.csv')
#print(SCAN.shape)
#print(SCAN.head())
scn_stations = SCAN['station'].unique().tolist()
SCAN['Date'] = pd.to_datetime(SCAN['Date'],format='%Y-%m-%d').apply(lambda x: x.date())
START_Date = SCAN['Date'].max()
START_DATE = str(START_Date)
dt3 = START_Date + timedelta(days=1)
start_date = str(dt3)
today = str(date.today())

# if data already up to date, no need proceed
if START_DATE == today:
    print('SCAN soil moisture data already up to date')
    sys.exit()

#param = ['SMS-2.0in', 'SMS-4.0in', 'SMS-8.0in', 'SMS-20.0in','SMS-40.0in']
param = 'SMS'

# ------------------ SOIL MOISTURE: SMS ------------------------
# params with depths are either: ['STX', 'STO', 'STV', 'STN', 'SMX', 'SMS', 'SMN', 'SMV']
# We just want 'SMS'
def SMS(scn_stations, param):
    # create the empty df that we will add new data for all stations
    data_df = pd.DataFrame()
    # list of possible depths with data
    depths = [-2.0, -4.0, -8.0, -20.0, -40.0]
    # for each station, get the soil moisture data for each depth
    for stn in scn_stations:
        # want only data from the previous date to today's date
        end_date = date.today()
        # empty df for this station
        sm_df = pd.DataFrame()
        # create Date column for all possible dates between where left off and today
        sm_df['Date'] = pd.date_range(start=start_date, end=end_date, freq='D')
        # now add the station as a column
        sm_df['station'] = stn
        # iterate through each depth to get data
        for depth in depths:
            try:
                # retrieving data from the api
                retval = client.service.getData(stationTriplets=stn, elementCd=param, ordinal=1,
                                                duration='DAILY', getFlags=False, beginDate=start_date,
                                                alwaysReturnDailyFeb29=False, endDate=end_date,
                                                heightDepth={'unitCd': 'in', 'value': depth})
                # getting the api data into a df
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
                # merge to the sm_df (which has the station column)
                # in other words, merge the data column with the correct station column
                sm_df = pd.merge(sm_df, temp_df, on='Date', how='outer')
            except:
                # just for fun, print statements to screen so user can see where missing data is
                print('NO DATA: {} for depth:{} and param: {}'.format(stn, depth, param))
        # add the current sm_df to the growing "data_df" before we change sm_df to an empty df for the next station
        data_df = data_df.append(sm_df)
    # may not be needed, but dropping rows where there is NO data for ALL soil depths
    filter_col = [col for col in data_df if col.startswith(param)]
    data_df.dropna(subset=filter_col, how='all', inplace=True)
    return data_df
# Now run the api function and save to output df
data_df = SMS(scn_stations, param)
# append the api df to the SCAN df
master_depth_var = SCAN.append(data_df)

# SAVE YOUR OUTPUT!
master_depth_var.to_csv(scan_path + 'SCAN_AL_SMS_only.csv', index=False)

# ------------------END:  SOIL MOISTURE: SMS ------------------------

if __name__ == "__main__":
    SMS(scn_stations, param)
