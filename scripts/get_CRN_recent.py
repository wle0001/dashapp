import pandas as pd
from datetime import date, datetime, timedelta
import sys
import numpy as np

# read in existing CRN df so we can add to it
crn_path = '/home/htdocs/aldrought/cr_scripts/'
ol_CRN = pd.read_csv(crn_path + 'CRN_AL_all.csv')
# since we read in the entire year thus far, just get the new dates
# CRN only updates to previous day. Today is only available tomorrow.
last_crn_date = str(ol_CRN['LST_DATE'].max())
last_real_date = datetime.strptime(last_crn_date,'%Y-%m-%d').date().isoformat()
last_Date = datetime.strptime(last_crn_date,'%Y-%m-%d').date() + timedelta(days=1)
last_date = last_Date.isoformat()
today = str(date.today())
#print('last date')
#print(last_date)


# if data already up to date, no need proceed
if last_date == today:
    print('CRN soil moisture data already up to date')
    sys.exit()


# Set up pathway to ftp sites
my_path = 'ftp://ftp.ncei.noaa.gov/pub/data/uscrn/products/daily01/'

# Info for table headers are found here as part of the my_path url above:
headers = '/HEADERS.txt'
# years of interest are 2009-2021 (years prior have no data for the 3 AL sites):
# we already have data for years past. Just want the latest
# get current year
year = str(date.today().year)

# Set up an empty dataframe with the appropriate headers:
# First row to be skipped, as it is just numbers. Column names are separated by whitespace
my_df = pd.read_csv(my_path + headers, skiprows=1, nrows=0, delim_whitespace=True)
cols = my_df.columns.to_list()

# making a copy of this for when we loop through years
CRN_df = my_df.copy()


# Create a function to grab the data for each of the 3 AL sites
def AL_sites(my_df, year):
    # 3 AL sites we are interested in
    AL_site_names = ['-AL_Fairhope_3_NE.txt', '-AL_Gadsden_19_N.txt', '-AL_Selma_13_WNW.txt']
    for site in AL_site_names:
        # Read in data for the AL site
        df2 = pd.read_csv(my_path + str(year) + "/CRND0103-" + str(year) + site, encoding="UTF-8",
                          delim_whitespace=True, names=cols)
        # getting just the base name of the file, i.e. the basic AL site name
        site_name = site.split('.')[0].split('-')[1]
        # for easy parsing later, we'll add the AL site name as a column. (example: AL_Fairhope_3_NE)
        df2['site'] = site_name
        # for easy parsing later, add a year column
        df2['year'] = str(year)
        # save data from each site to the growing dataframe
        my_df = my_df.append(df2)
    # getting date column same format as the input "ol_CRN"
    my_df['LST_DATE'] = pd.to_datetime(my_df['LST_DATE'], format='%Y%m%d').apply(lambda x: x.date())
    return my_df


# Now want the data from the AL_sites for this year.
# Get the data and add the header
CRN_df = CRN_df.append(AL_sites(my_df, year))
# Get just the new entries (remember, this grabbed everything from this year)
new_CRN = CRN_df[CRN_df['LST_DATE'] >= last_Date]
#print(new_CRN.shape)
# Now append the new and the old
new_CRN = ol_CRN.append(new_CRN)
# replace -9999.0 to nan
new_CRN = new_CRN.replace({-9999.0: np.nan})
# Save your dataframe:
new_CRN.to_csv(crn_path + 'CRN_AL_all.csv', index=False)

if __name__ == "__main__":
    AL_sites(my_df, year)
