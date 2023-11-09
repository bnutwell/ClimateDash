# import relevant functions
import panel as pn
import hvplot.pandas
import pandas as pd
import numpy as np
import jupyter_bokeh
import matplotlib.pyplot as plt
from bokeh.io import curdoc
from bokeh.io import output_notebook
from bokeh.models import HoverTool
hvplot.extension('bokeh')

pn.extension(design='bootstrap')


# load sample vehicle data
csv_file = ("Vehicles_data.csv")
veh_data = pd.read_csv(csv_file)
veh_list = list(veh_data['Vehicle Type'])
veh_list_ev = list(veh_data[veh_data['FE_Unit']=='MPKWh']['Vehicle Type'])
veh_list_ice = list(veh_data[veh_data['FE_Unit']=='MPG']['Vehicle Type'])

# load zip code energy coefficient lookup data in kg-CO2 / kWh
csv_file = ("zip_coefficients.csv")
grid_coeff_data = pd.read_csv(csv_file)

# establish other lookup coefficients
# fossil fuels
natgas_co2_coeff = 5.5      # carbon emissions kg-CO2 / ccf
natgas_kwh_coeff = 14       # energy equivalent kWh / ccf
petrol_kwh_coeff = 33.8     # energy equivalent kWh / gal
petrol_co2_coeff = 8.887    # carbon emissions kg-CO2 / gal
pubtrans_co2_coeff = 0.1    # carbon emissions kg-CO2 / mile / passenger
pubtrans_fe = 90.0          # fuel burned mile / gal / passenger
air_co2_coeff = 250.0       # carbon emissions kg-CO2 / hour in flight
air_fe_rate = 36.0          # fuel burned gal / hour in flight

# food
diet_co2_eq = [0.69,1.16,1.66,2.23,2.62,2.91]   # kg-CO2 / 1000 Kcal
diet_prod_mult = [d*8/2.23 for d in diet_co2_eq]  # 8:1 food production/nutrition ratio for omnivore, scaled to other diets by CO2
diet_names = ['vegan','vegetarian','pescetarian','omnivore','paleo','keto']
diet_kcal_to_kwh = 0.001162     # W-h/cal = kwh/kcal
# targets
weekly_target_kwh = 2*24*7      # 2000 Watt Society target
weekly_target_W = 2000          # 2000 Watt Society target
weekly_target_CO2 = 2500*7/365  # 1 metric ton / year / person

# useful conversion factors
kwh_to_watts = 1000/(24*7)      # convert from kWh to watts
month_to_week = 12*7/365        # convert from monthly rate to weekly
year_to_week = 7/365

# establish design parameters
intwidth = 100
textcolor = 'black'
backcolor1 = 'darkgrey'
backcolor2 = 'lightgrey'

# function to return grid emissions coefficient in (kg-CO2 / kWh) for a given ZIP code
def coeff_lookup(coeff_data,zip=43017):
    if zip in coeff_data['zip'].values:
        rows = coeff_data[coeff_data['zip']==zip]
        return rows['Coefficient'].iloc[0]
    else:
        return 0.5555

# function to check if a vehicle is electric or gas powered    
def get_veh_type(veh_data,model):
    rows = veh_data[veh_data['Vehicle Type']==model]    
    if rows['FE_Unit'].iloc[0]=='MPKWh':
        return 'EV'
    else:
        return 'ICE'

def check_ev(vt):
    type = get_veh_type(veh_data,vt)
    if type == 'EV':
        return True
    else:
        return False

# multipurpose function to return vehicle fuel usage given model, mileage, and % highway driving
#   if vehicle fuel economy units are MPKWh (electric vehicles):
#       if retval='kwh' (default), returns usage in kWh
#       if retval='gal', returns 0
#       if retval='co2', looks up the grid emisions coefficient and returns kg-CO2
#   if vehicle fuel economy units are MPG (gas /hybrid vehicles):
#       if retval = 'gal', returns usage in gallons for vehicles with MPG economy units or 0 for EVs
#       if retval = 'kwh' (default), returns usage in kwh
#       if retval = 'co2', returns CO2 emissions in kg based on petrol CO2 coefficient
#   optionally scales output by timeconv value (such as yearly-to-weekly)
#
def get_veh_usage(veh_data,model,mileage,pct_hwy,retval='kwh',timeconv=1,zip=0):

    rows = veh_data[veh_data['Vehicle Type']==model]
    hwy_fe = rows['FE_Highway'].iloc[0]
    city_fe = rows['FE_City'].iloc[0]
    fe = hwy_fe*pct_hwy/100 + city_fe*(1-pct_hwy/100)
    fuel_usage = mileage / fe * timeconv

    if rows['FE_Unit'].iloc[0]=='MPKWh':
        if retval == 'kwh':
            return round(fuel_usage,1)
        elif retval == 'gal':
            return 0
        elif retval == 'co2':
            zipcoeff = coeff_lookup(grid_coeff_data,zip)
            return round(fuel_usage*zipcoeff,1)
    else:
        if retval == 'kwh':
            return(round(fuel_usage*petrol_kwh_coeff,1))
        elif retval == 'gal':
            return round(fuel_usage,1)
        elif retval == 'co2':
            return round(fuel_usage*petrol_co2_coeff,1)

# function to multiply values during responsive notebook usage
def convert(inputval,conversion1,conversion2 = 1):
    return round(inputval * conversion1 * conversion2,1)

def arraysum(inputarray):
    asum = 0.0
    for i in inputarray:
        asum+=i
    return asum

# function to look up a value from a list
def list_lookup(list_data,ind=1):
    if ind <= len(list_data):
        return list_data[ind]
    else:
        return list_data[0]

# function to plot the output during responsive usage
def plot_usage(inputs, usage, sources, pop=2):

# TODO  figure out how to apply styling theme

    # create the dictionary
    consumption = {inputs[i]:np.array([convert(usage[i],kwh_to_watts,1/pop),0]) for i in range(len(inputs))}
    #consumption = {inputs[i]:np.array([usage[i],0]) for i in range(len(inputs))}
    consumption['Target'] = np.array([0,weekly_target_W])
    condf = pd.DataFrame(consumption)
    condf.index=sources
    hover = HoverTool()
    fig = condf.hvplot.bar(height=500, width=400, legend=True,stacked=True,
                           title='Total Power Consumption (W)',
                           tools=[hover])
    #fig.theme = 'dark minimal'
    #fig=condf
    return fig

# function to calculate total power demand based on user inputs
#   and create a stacked bar chart
#   input variables are the user input widgets which pass dynamic values
def plot_usage_2(t1,h1,m1,
                t2,h2,m2,
                t3,h3,m3,
                t4,h4,m4,
                pt,at,
                he,hg,
                pop=2,
                hd=2000,hdt=4
                ):
    # check vehicle types and make a list
    tv = []
    tv.append(get_veh_type(veh_data,t1))
    tv.append(get_veh_type(veh_data,t2))
    tv.append(get_veh_type(veh_data,t3))
    tv.append(get_veh_type(veh_data,t4))
    # convert user inputs to vehicle consumption in watts and make a list
    wv = []
    wv.append(get_veh_usage(veh_data,t1,m1,h1,timeconv=year_to_week)*kwh_to_watts)
    wv.append(get_veh_usage(veh_data,t2,m2,h2,timeconv=year_to_week)*kwh_to_watts)
    wv.append(get_veh_usage(veh_data,t3,m3,h3,timeconv=year_to_week)*kwh_to_watts)
    wv.append(get_veh_usage(veh_data,t4,m4,h4,timeconv=year_to_week)*kwh_to_watts)
    # calculate the stacked bar totals in watts
    # all amortized across household population (except daily calories which is already individual)
    wve = sum([wv[i] for i in range(4) if tv[i]=='EV'])/pop                 # vehicle electric
    wvg = sum([wv[i] for i in range(4) if tv[i]!='EV'])/pop                 # vehicle gas
    wp = pt/pubtrans_fe*petrol_kwh_coeff*year_to_week*kwh_to_watts/pop      # public transit
    wa = at*air_fe_rate*petrol_kwh_coeff*year_to_week*kwh_to_watts/pop      # air travel
    whe = he*month_to_week*kwh_to_watts/pop                                 # household electric
    whg = hg*natgas_kwh_coeff*month_to_week*kwh_to_watts/pop                # household gas
    whd = hd*diet_kcal_to_kwh*list_lookup(diet_prod_mult,hdt)*kwh_to_watts*7 # diet, *7 = day to week
    # create the dictionary
    consumption = {'EV Grid':np.array([wve,0]),
                   'ICE Fuel Usage':np.array([wvg,0]),
                   'Public Transit':np.array([wp,0]),
                   'Air Travel':np.array([wa,0]),                                      
                   'HH Elec Grid':np.array([whe,0]),
                   'HH NatGas Usage':np.array([whg,0]),
                   'HH Diet Impact':np.array([whd,0]),                   
                   '2000-W Target':np.array([0,weekly_target_W])}
    condf = pd.DataFrame(consumption)
    condf.index=['Your\nUsage\n','2000-W\nTarget\n']
    fig = condf.hvplot.bar(height=600, width=400, legend=True,stacked=True,
                           title='Total Power Consumption (W) per HH member')

    return fig


# function to calculate total power demand based on user inputs
#   and create a stacked bar chart
#   input variables are the user input widgets which pass dynamic values
def plot_co2(t1,h1,m1,
            t2,h2,m2,
            t3,h3,m3,
            t4,h4,m4,
            pt,at,
            he,hg,zip,
            pop=2,
            hd=2000,hdt=4
            ):
    
    zipcoeff = coeff_lookup(grid_coeff_data,zip)
    # check vehicle types and make a list
    tv = []
    tv.append(get_veh_type(veh_data,t1))
    tv.append(get_veh_type(veh_data,t2))
    tv.append(get_veh_type(veh_data,t3))
    tv.append(get_veh_type(veh_data,t4))    
    # convert user inputs to vehicle consumption in kg-CO2 and make a list
    cv = []
    cv.append(get_veh_usage(veh_data,t1,m1,h1,timeconv=year_to_week,retval='co2',zip=zip))
    cv.append(get_veh_usage(veh_data,t2,m2,h2,timeconv=year_to_week,retval='co2',zip=zip))
    cv.append(get_veh_usage(veh_data,t3,m3,h3,timeconv=year_to_week,retval='co2',zip=zip))
    cv.append(get_veh_usage(veh_data,t4,m4,h4,timeconv=year_to_week,retval='co2',zip=zip))
    # calculate the stacked bar totals in weekly kg-CO2
    # all amortized across household population (except daily calories which is already individual)
    cve = sum([cv[i] for i in range(4) if tv[i]=='EV'])/pop     # vehicle electric
    cvg = sum([cv[i] for i in range(4) if tv[i]!='EV'])/pop     # vehicle gas
    cpt = pt/pubtrans_fe*petrol_co2_coeff*year_to_week/pop      # public transit
    cat = at*air_fe_rate*petrol_co2_coeff*year_to_week/pop      # air travel
    che = he*month_to_week*zipcoeff/pop                         # household electric
    chg = hg*natgas_co2_coeff*month_to_week/pop                 # household gas
    chd = hd*list_lookup(diet_co2_eq,hdt)*7/1000                # diet, *7 = day to week
    # create the dictionary
    consumption2 = {'EV Grid':np.array([cve,0]),
                   'ICE Fuel Usage':np.array([cvg,0]),
                   'Public Transit':np.array([cpt,0]),
                   'Air Travel':np.array([cat,0]),                                      
                   'HH Elec Grid':np.array([che,0]),
                   'HH NatGas Usage':np.array([chg,0]),
                   'HH Diet Impact':np.array([chd,0]),                   
                   'Global Target':np.array([0,weekly_target_CO2])}
    condf2 = pd.DataFrame(consumption2)
    condf2.index=['Your\nUsage\n','2.5t kg-CO2/year\nTarget\n']
    fig2 = condf2.hvplot.bar(height=600, width=400, legend=True,stacked=True,
                           title='Weekly CO2 emissions (kg) per HH member')

    return fig2

def plot3(h):
    # create the dictionary
    consumption3 = {'EV Grid':np.array([100,0]),
                   'New Target':np.array([0,300])}
    condf3 = pd.DataFrame(consumption3)
    condf3.index=['Your\nUsage\n','Fake\nTarget\n']
    fig3 = condf3.hvplot.bar(height=600, width=400, legend=True,stacked=True,
                           title='Fictitious Climate Impact #3')

    return fig3