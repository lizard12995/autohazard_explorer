import carto2gpd
import geopandas as gpd
import pandas as pd
import numpy as np
import datetime as dt

from matplotlib import pyplot as plt

import hvplot.pandas
import holoviews as hv

import esri2gpd
import seaborn as sns



# Load, clean, wrangle city data

carto_url = "https://phl.carto.com/api/v2/sql"



## Licenses

table_name = "business_licenses"
where = "licensetype IN ('Hazardous Materials', 'Motor Vehicle Repair / Retail Mobile Dispensing', 'Auto Wrecking / Junk Yard') AND mostrecentissuedate >= current_date - 1460"
licenses = carto2gpd.get(carto_url, table_name, where=where)

drop = ["rentalcategory","numberofunits","owneroccupied","ownercontact1name",
       "ownercontact1mailingaddress","ownercontact1mailingaddress","ownercontact1city",
       "ownercontact1state", "ownercontact1zippostalcode",
       "ownercontact2name","ownercontact2mailingaddress","ownercontact2mailingaddress","ownercontact2city",
       "ownercontact2state", "ownercontact2zippostalcode", "council_district","posse_jobid"]

licenses2 = licenses.drop(drop, axis=1)
licenses2 = licenses2.loc[(licenses["parcel_id_num"] != "RETIRED")].copy()

### Get license type x status by OPA Account
acct_lic_wide = licenses2.groupby(["opa_account_num", 
                                    "opa_owner","licensetype",
                                   "licensestatus"]).size().unstack(["licensetype","licensestatus"])

acct_lic_wide.columns=acct_lic_wide.columns.map('_'.join)
acct_lic_wide=acct_lic_wide.reset_index()

### Create active indicators then merge
acct_active = licenses2.groupby(["opa_account_num", 
                                 "licensestatus"]).size().unstack(["licensestatus"]).reset_index()

acct_active["Active_TF"] = np.where(acct_active["Active"].isna(),"Not Active","Active")

acct_lic2 = acct_active.merge(acct_lic_wide, how='left').drop(columns=["opa_owner"])

### Append info
biz_name = licenses2[["opa_account_num","business_name"]]

#### Roll up multiple business names
biz_name['business_name'] = biz_name['business_name'].fillna("NA")
biz_name = biz_name.groupby(biz_name["opa_account_num"],as_index=False)['business_name'].apply(lambda x: ', '.join(x))

licinfo=licenses2[["opa_account_num","opa_owner","address","geometry"]]
licinfo=licinfo.merge(biz_name, how='left')

acct_lic = acct_lic2.merge(licinfo, on="opa_account_num", how='left')

acct_lic=acct_lic.drop_duplicates()



## 311 complaints

table_name = "public_cases_fc"
where = "requested_datetime >= current_date - 1460 AND service_name IN ('Abandoned Vehicle','LI Escalation', 'Other (Streets)', 'Illegal Dumping','Sanitation / Dumpster Violation','Rubbish/Recyclable Material Collection', 'Rubbish/Recyclable Material Collection','Dangerous Building Complaint', 'Maintenance Complaint','Construction Complaints', 'Complaint (Streets)', 'Miscellaneous','Maintenance Residential or Commercial','Zoning Business', 'Building Dangerous','Fire Safety Complaint','Vacant House or Commercial','License Complaint', 'Building Force','Fire Residential or Commercial', 'Zoning Residential','Right-of-Way', 'Dangerous Sidewalk','Sanitation Violation','Dumpster Violation',  'Other Dangerous', 'License_Complaint', 'Vacant Lot Clean-Up', 'Fire_Safety_Complaint')"
complaints = carto2gpd.get(carto_url, table_name, where=where)

#Drop irrelevant - status just means whether it has gone to proper dept
complaints = complaints.drop(["cartodb_id","objectid","status","status_notes", "service_code",
                             "updated_datetime", "expected_datetime"], axis=1)

#For later merge with L&I complaints
complaints["service_request_id"] = complaints["service_request_id"].astype("str")



## L&I complaints

proplist = acct_lic["opa_account_num"]

#Codes related to auto body
indcodes = ['HAZARDOUS MATERIAL','SCRAP YARD',
            'ILLEGAL BUSINESS',
            "NUISANCE PROPERTY UNIT"]
#Code for "NOT" code:
notcodes = ['MAINTENANCE RESIDENTIAL',  'NO HEAT', 'VACANT HOUSE',
            'DRAINAGE MAINTENANCE RESIDENTIAL TO HCEU','INFESTATION RESIDENTIAL', 
            'VACANT LOT RESIDENTIAL','SIGNAGE', 'TREE DANGEROUS OCCUPIED',
            'DAY CARE COMMERCIAL', 'TREE DANGEROUS',  'BOARDING OR ROOMING HOUSE', 
            'VACANT HOUSE RESIDENTIAL', 'BUGS OR MICE', 
            'WATER IN BASEMENT RESIDENTIAL','ROOF LEAK RESIDENTIAL',
            'HIGH GRASS OR WEEDS RESIDENTIAL', 'LEAD ABATEMENT HEALTH DEPT',
            'DECK CONSTRUCTION', 'TREE FALLING SPECIFY AREA OF PROPERTY',
            'STAGNANT POOL WATER', 'NO RENTAL LICENSE',
            'OCCUPIED RESIDENCE WITHOUT HEAT','BLOCKED DRAIN RESIDENTIAL',
            'REDEVELOPMENT AUTHORITY - VACANT HOUSE CONDEMNATION',
            'SPECIAL VACANT HOUSE','SPECIAL MAINTENANCE RESIDENTIAL', 
            'SPECIAL VACANT LOT RESIDENTIAL','LICENSE RESIDENTIAL',
            'DAYCARE CENTER COMMERCIAL','RESIDENTIAL STRUCTURAL ASSESSMENT', 
            'BLOCKED DRAIN COMMERCIAL','FIRE SAFETY COMPLAINT MULTI FAMILY DWELLING',
            'PROPERTY MAINTENANCE HIGH WEEDS', 'VENDOR COMPLAINT',
            'DEMOLITION COMPLAINTS', 'GRAFFITI','FIRE SAFETY COMPLAINT HIGH RISE',
            'FIRE SAFETY COMPLAINT ASSEMBLY SPACE', 'PLASTIC BAG COMPLAINT',
            'BOARDING/ROOMING HOUSE']
notcodes = tuple(notcodes)

#Pull from API
table_name = "complaints"
where = "complaintdate >= current_date - 1460 AND NOT complaintcodename IN {}".format(notcodes)
LIcomplaints = carto2gpd.get(carto_url, table_name,where=where)

#Drop columns
LIcomplaints = LIcomplaints.drop(["cartodb_id", "objectid","systemofrecord",
                                 "council_district","posse_jobid"],axis=1)

#Not in license list but have violation
LIcomplaints_codes = LIcomplaints.loc[(LIcomplaints["complaintcodename"].isin(indcodes)) 
                                      & ~(LIcomplaints["opa_account_num"].isin(proplist))].copy().reset_index()

#For final df:
#extract list of opa_account_num
code_proplist = LIcomplaints_codes["opa_account_num"].unique()

#Make it a dataframe
props_LIcomplaint = pd.DataFrame(code_proplist).rename(columns={0:"opa_account_num"})

#Filter to opa_account_num in license list or in code list
LIcomplaints_filt = LIcomplaints.loc[(LIcomplaints["opa_account_num"].isin(proplist) |
                        LIcomplaints["opa_account_num"].isin(code_proplist))].copy().reset_index()

#Info to merge with opa_account_nums
LIinfo = LIcomplaints_filt[["opa_account_num","opa_owner","address","geometry"]].drop_duplicates()
LIinfo = LIinfo.dropna(subset=["opa_account_num"])

#use this later to merge with license data
props_LI_c = LIinfo.merge(props_LIcomplaint,how="right", on="opa_account_num")

#Merge with 311 calls
#NOTE: Not all complaints are from 311 calls
LIcomplaints_311 = LIcomplaints_filt.merge(complaints, left_on="ticket_num_311",right_on="service_request_id",
                                          how='left')

#Number complaints per account
#Groupby
summary_LIcomplaints = LIcomplaints_311.groupby("opa_account_num",
                                                     as_index=False).size().rename(columns=
                                                                                   {"size":"number_complaints"})

#Indicator for whether it was a 311 call
LIcomplaints_311["called"] = np.where(LIcomplaints_311["service_request_id"].isna(), "F","T")

#whether or not 311 was called?
summary_311LIcomplaints = LIcomplaints_311.groupby(
    ["opa_account_num","called"]).size().unstack("called").reset_index()

summary_LIcomplaints = summary_LIcomplaints.merge(summary_311LIcomplaints)

#Rename cols; use me later
summary_LIcomplaints = summary_LIcomplaints.rename(columns={"F":"311_F","T":"311_T"})
summary_LIcomplaints["perc_311"] = (summary_LIcomplaints["311_T"]/summary_LIcomplaints["number_complaints"])*100
summary_LIcomplaints = summary_LIcomplaints.drop(columns=["311_F","311_T"])

#Time to investigation

#Convert to datetime
for i in ['initialinvestigation_date', 'complaintdate', 'complaintresolution_date']:
    LIcomplaints_filt[i] = pd.to_datetime(LIcomplaints_filt[i])

#Create new cols for time to investigation and resolution
LIcomplaints_filt["time_to_invest"] = LIcomplaints_filt["initialinvestigation_date"] - LIcomplaints_filt["complaintdate"]

LIcomplaints_filt["time_to_resolution"] = LIcomplaints_filt["complaintresolution_date"] - LIcomplaints_filt["complaintdate"]

#Only positive response times, no negative
#Sometimes, investigation date is AFTER complaint date
LIcomplaints_pos = LIcomplaints_filt.loc[(LIcomplaints_filt["initialinvestigation_date"] >= LIcomplaints_filt["complaintdate"])].copy()

#Only NA for investigation
NAinvest = LIcomplaints_filt.loc[(LIcomplaints_filt["initialinvestigation_date"].isna())].copy()
NAinvest = NAinvest.groupby("opa_account_num", as_index=False).size().rename(columns={"size":"no_investigation"})

#Only NA for resolution
NAresolve = LIcomplaints_filt.loc[(LIcomplaints_filt["complaintresolution_date"].isna())].copy()
NAresolve = NAresolve.groupby("opa_account_num", as_index=False).size().rename(columns={"size":"no_resolution"})

#Response to complaint time by opa_account_num
#mean_time_to_investigation
prop_time = LIcomplaints_pos.groupby(["opa_account_num"],
            as_index=False)["time_to_invest"].mean().sort_values(by="time_to_invest",ascending=False)

#Number of investigated complaints per opa
#Yields "number_complaints_investigated" column
number_invest = LIcomplaints_pos.groupby(["opa_account_num"],
                as_index=False).size().rename(columns={"size":"number_complaints_investigated"})

#Time from complaint to resolution for POSITIVE TIME complaints
#time_to_resolution
resolve_time = LIcomplaints_filt.groupby(["opa_account_num"],
                as_index=False)["time_to_resolution"].mean().sort_values(by="time_to_resolution",ascending=False)

#Number of ALL complaints resolved
#number_complaints_resolved
number_resolve = LIcomplaints_filt.loc[~(LIcomplaints_filt["complaintresolution_date"].isna())]
number_resolve = number_resolve.groupby(["opa_account_num"],
                as_index=False).size().rename(columns={"size":"number_complaints_resolved"})

#Merge together: NAs, number investigations, time to investigtation, number complaints
summary_LIcomplaints2 = summary_LIcomplaints.merge(NAinvest,
    how='left').merge(number_invest, how='left').merge((prop_time),how='left').rename(
    columns={"time_to_invest":"mean_time_to_investigation"})

#Add info on resolution
summary_LIcomplaints2 = summary_LIcomplaints2.merge(number_resolve,
         how='left').merge(NAresolve,how='left').merge(resolve_time,how="left")


## L&I Investigations

table_name = "case_investigations"
where = "investigationcompleted >= current_date - 1460"
LIinvest = carto2gpd.get(carto_url, table_name, where=where)

#Remove some columns
LIinvest = LIinvest.drop(["posse_jobid","council_district","systemofrecord",
                         "addressobjectid","objectid","cartodb_id"], axis=1)

#investigations/account
LIinvest_filt = LIinvest.loc[(LIinvest["opa_account_num"].isin(proplist) |
                        LIinvest["opa_account_num"].isin(code_proplist))].copy().reset_index()

LIcomplaints_filtNA = LIcomplaints_filt.loc[~(LIcomplaints_filt["initialinvestigation_date"].isna())]

#Groupby
summary_LIinvest = LIinvest_filt.groupby("opa_account_num", as_index=False).size().rename(columns={"size":"overall_num_investigations"})


## L&I Violations

table_name = "violations"
where = "casecreateddate >= '2018-01-01'"
LIviolation = carto2gpd.get(carto_url, table_name, where=where)

LIviolation_filt = LIviolation.loc[(LIviolation["opa_account_num"].isin(proplist) |
                        LIviolation["opa_account_num"].isin(code_proplist))].copy().reset_index()

#Groupby OPA and caseprioritydesc
summary_LIviolation = LIviolation_filt.groupby(["opa_account_num", "caseprioritydesc"]).size().unstack().reset_index()
summary_LIviolation2 = LIviolation_filt.groupby(["opa_account_num"],as_index=False).size().rename(
    columns={"size":"total_violations"})
summary_LIviolation = summary_LIviolation.merge(summary_LIviolation2,how="left").fillna(0)


# Pulling it all together

OPA = pd.concat([acct_lic, props_LI_c]).dropna(subset=["geometry"]).fillna(0)

#Reorder columns
OPA = OPA[['opa_account_num', 'opa_owner','business_name', 'address','License', 'geometry', 'Active', 'Closed', 'Expired',
       'Inactive', 'Revoked','Active_TF',
       'Motor Vehicle Repair / Retail Mobile Dispensing_Inactive',
       'Motor Vehicle Repair / Retail Mobile Dispensing_Active',
       'Hazardous Materials_Expired',
       'Motor Vehicle Repair / Retail Mobile Dispensing_Expired',
       'Hazardous Materials_Active', 'Hazardous Materials_Inactive',
       'Auto Wrecking / Junk Yard_Inactive', 'Hazardous Materials_Closed',
       'Auto Wrecking / Junk Yard_Active',
       'Auto Wrecking / Junk Yard_Revoked',
       'Motor Vehicle Repair / Retail Mobile Dispensing_Closed',
       'Auto Wrecking / Junk Yard_Expired',
       'Motor Vehicle Repair / Retail Mobile Dispensing_Revoked',
       'Auto Wrecking / Junk Yard_Closed', 'Hazardous Materials_Revoked']]

df = OPA.merge(summary_LIcomplaints2, how='left').merge(summary_LIinvest,how='left').merge(
    summary_LIviolation, how='left')

df["mean_time_to_investigation"]=df["mean_time_to_investigation"].dt.days
df["time_to_resolution"]=df["time_to_resolution"].dt.days

#Fill NA values with zeroes
f = [c for c in df.columns if c not in ['mean_time_to_investigation','time_to_resolution']]
df[f] = df[f].fillna(0)

#export as csv
df.to_csv('upd_li_props.csv', index = False)

df = gpd.GeoDataFrame(df, crs="EPSG:4326").to_crs(epsg=3857)

#export as geojson
df.to_file("upd_li_props.geojson", driver='GeoJSON')
