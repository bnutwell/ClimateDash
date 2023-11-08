# Climate Dashboard prototype notebook

# import relevant functions
import panel as pn
import hvplot.pandas
import pandas as pd
import numpy as np
import jupyter_bokeh
import matplotlib.pyplot as plt
from bokeh.io import curdoc
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

# widget to input ZIP code and get coefficient
ZIP_entry = pn.widgets.IntInput(name="ZIP Code",
                                value=43017,width=intwidth,
                                styles={'color':textcolor})

##### Section 1 - Vehicles #################################

# widgets to specify vehicle #1 usage
v1t = pn.widgets.Select(name='Vehicle #1 Type',options=veh_list,value='SUV-Compact-ICE').servable
v1m = pn.widgets.IntSlider(name="Annual Mileage",value=0,start=0,end=30000,step=1000)
v1h = pn.widgets.IntSlider(name='% Highway Driving',value=50,start=0,end=100,step=5)
# detect vehicle fuel type, calculate energy usage and CO2
v1f = pn.bind(get_veh_type,veh_data,v1t)
v1_isev = pn.bind(check_ev,v1t)
v1g = pn.bind(get_veh_usage,veh_data,v1t,v1m,v1h,
                retval='gal',timeconv=year_to_week)  # direct calc yearly gas usage gal
v1k = pn.bind(get_veh_usage,veh_data,v1t,v1m,v1h,
                retval='kwh',timeconv=year_to_week)  # direct calc yearly kwh
v1c = pn.bind(get_veh_usage,veh_data,v1t,v1m,v1h,
                retval='co2',zip=ZIP_entry,timeconv=year_to_week)   # grid emissions co2

# create pretty text widgets to show the vehicle coefficients
fuel_text1a = pn.widgets.StaticText(name = "Vehicle weekly fuel (gal)",value=12)
#fuel_text1a = pn.widgets.StaticText(name = "Vehicle weekly fuel (gal)",value=v1g)
fuel_text1b = pn.widgets.StaticText(name = "Vehicle weekly energy (kWh)",value=v1k)
co2_text1 = pn.widgets.StaticText(name = "Indirect weekly emissions (kg CO2)",value=v1c)    

# widgets to specify vehicle #2 usage
v2t = pn.widgets.Select(name='Vehicle #2 Type',options=veh_list,value='SUV-Compact-ICE')
v2m = pn.widgets.IntSlider(name="Annual Mileage",value=0,start=0,end=30000,step=1000)
v2h = pn.widgets.IntSlider(name='% Highway Driving',value=50,start=0,end=100,step=5)

# widgets to specify vehicle #3 usage
v3t = pn.widgets.Select(name='Vehicle #3 Type',options=veh_list,value='SUV-Compact-ICE')
v3m = pn.widgets.IntSlider(name="Annual Mileage",value=0,start=0,end=30000,step=1000)
v3h = pn.widgets.IntSlider(name='% Highway Driving',value=50,start=0,end=100,step=5)

# widgets to specify vehicle #4 usage
v4t = pn.widgets.Select(name='Vehicle #4 Type',options=veh_list,value='SUV-Compact-ICE')
v4m = pn.widgets.IntSlider(name="Annual Mileage",value=0,start=0,end=30000,step=1000)
v4h = pn.widgets.IntSlider(name='% Highway Driving',value=50,start=0,end=100,step=5)

# widgets to specify public transportation usage
ptm = pn.widgets.IntSlider(name="Bus/Train Annual Rider Mileage",value=0,start=0,end=20000,step=500)
ptc = pn.bind(convert,ptm,pubtrans_co2_coeff,year_to_week)      # direct emissions co2
ptk1 = pn.bind(convert,ptm,1/pubtrans_fe,year_to_week)          # fuel consumption, gal
ptk2 = pn.bind(convert,ptk1,petrol_kwh_coeff)                   # equivalent kwh
pt_text1a = pn.widgets.StaticText(name = "Public Transit weekly fuel (gal)",value=ptk1)
pt_text1b = pn.widgets.StaticText(name = "Public Transit weekly energy (kWh)",value=ptk2)
pt_text2 = pn.widgets.StaticText(name = "Public Transit weekly emissions (kg CO2)",value=ptc)

# widgets to specify air travel usage
ath = pn.widgets.IntSlider(name="Air Travel Annual Flight Hours",value=0,start=0,end=200,step=10)
atc = pn.bind(convert,ath,air_co2_coeff,year_to_week)      # direct emissions co2
atk1 = pn.bind(convert,ath,air_fe_rate,year_to_week)          # fuel consumption, gal
atk2 = pn.bind(convert,atk1,petrol_kwh_coeff)                   # equivalent kwh
at_text1a = pn.widgets.StaticText(name = "Air Travel weekly fuel (gal)",value=atk1)
at_text1b = pn.widgets.StaticText(name = "Air Travel weekly energy (kWh)",value=atk2)
at_text2 = pn.widgets.StaticText(name = "Air Travel weekly emissions (kg CO2)",value=atc) 

##### Section 2 - Household #################################

# bind the coefficient output to the lookup function and input
ZIP_coeff = pn.bind(coeff_lookup,grid_coeff_data,ZIP_entry)
# create a pretty text widget to show the grid coefficient
ZIP_text = pn.widgets.StaticText(name = "Local kg-CO2/kWh Coefficient",value=ZIP_coeff)

# widget to enter monthly energy usage
hhe = pn.widgets.IntSlider(name="Monthly Home Electric Usage (kWh)",value=0,start=0,end=2000,step=50)
# calculate usage
hhelectric_co2 = pn.bind(convert,hhe,ZIP_coeff,12/52)
hhelectric_kwh = pn.bind(convert,hhe,12/52)

# widget to enter monthly natural gas usage
hhn = pn.widgets.IntSlider(name="Monthly Home Natural Gas Usage (ccf)",value=0,start=0,end=200,step=5)
# calculate usage
hhnatgas_co2 = pn.bind(convert,hhn,natgas_co2_coeff,12/52)
hhnatgas_kwh = pn.bind(convert,hhn,natgas_kwh_coeff,12/52)

# create pretty text widgets to show the vehicle coefficients
hh_text1 = pn.widgets.StaticText(name = "HH weekly electric (kg CO2)",value=hhelectric_co2)
hh_text2 = pn.widgets.StaticText(name = "HH weekly electric (kWh)",value=hhelectric_kwh)
hh_text3 = pn.widgets.StaticText(name = "HH weekly natural gas emissions (kg CO2)",value=hhnatgas_co2)
hh_text4 = pn.widgets.StaticText(name = "HH weekly natural gas power (kWh)",value=hhnatgas_kwh)

# widget to enter household population
hh_pop = pn.widgets.IntSlider(name="Number of Adults living in home",value=1,start=1,end=10,step=1)

# widget to enter daily diet (in calories) per adult
hhd = pn.widgets.IntSlider(name="Daily Calorie Intake (per adult)",value=0,start=1000,end=5000,step=250)

# widget to enter daily diet type
hhdt = pn.widgets.IntSlider(name="Diet Type",value=4,start=1,end=6,step=1)

# calculate usage
# retrieve the dietary coefficient
# then multiply by the num of calories and convert from daily to monthly
hhdiet_co2_coeff = pn.bind(list_lookup,diet_co2_eq,hhdt)
hhdiet_prod_coeff = pn.bind(list_lookup,diet_prod_mult,hhdt)
hhdiet_co2 = pn.bind(convert,hhd,hhdiet_co2_coeff,0.001*7)
hhdiet_kwh = pn.bind(convert,hhd,hhdiet_prod_coeff,diet_kcal_to_kwh*7)

# create pretty text widgets to show the vehicle coefficients
hh_text5 = pn.widgets.StaticText(name = "HH weekly diet (kg CO2)",value=hhdiet_co2)
hh_text6 = pn.widgets.StaticText(name = "HH weekly diet (kWh)",value=hhdiet_kwh)

# create a plot of the total energy consumption
fig = pn.bind(plot_usage_2,
            v1t,v1h,v1m,
            v2t,v2h,v2m,
            v3t,v3h,v3m,
            v4t,v4h,v4m,
            ptm,ath,
            hhe,hhn,hh_pop,
            hhd,hhdt
            )

# create a plot of the total energy consumption
fig2 = pn.bind(plot_co2,
            v1t,v1h,v1m,
            v2t,v2h,v2m,
            v3t,v3h,v3m,
            v4t,v4h,v4m,
            ptm,ath,
            hhe,hhn,
            ZIP_entry,
            hh_pop,
            hhd,hhdt
            )

fig3 = pn.bind(plot3,hhe)

# create layout for the worksheets
pn.Tabs(
    pn.Row(
        pn.layout.Spacer(width=50),        
        pn.Column(
            '## Personal Vehicles',
            v1t,v1h,v1m,
            fuel_text1a,fuel_text1b,co2_text1,
            pn.layout.Spacer(height=30),
            v2t,v2h,v2m,
            pn.layout.Spacer(height=30),
            v3t,v3h,v3m,
            pn.layout.Spacer(height=30),            
            styles={'background': 'black'}
        ),
        pn.layout.Spacer(width=50),        
        pn.Column(
            '## Mass Transit',
            ptm,
            pt_text1a,pt_text1b,pt_text2,
            pn.layout.Spacer(height=30),
            ath,
            at_text1a,at_text1b,at_text2,
            pn.layout.Spacer(height=30),
            styles={'background': 'black'}
        ),
        pn.layout.Spacer(width=50),        
        pn.Column(
            '## Your Results',
            fig,
            styles={'background': 'black'}
        ),
        pn.layout.Spacer(width=50),        
        dynamic = True,styles={'background': 'black'},
        name = 'Transportation'
    ),
    pn.Row(
        pn.layout.Spacer(width=50),
        pn.Column(
            '## Household',
            ZIP_entry,ZIP_text,
            pn.layout.Spacer(height=30),
            hh_pop,
            pn.layout.Spacer(height=30),
            hhe,hh_text2,hh_text1,
            hhn,hh_text4,hh_text3,
            pn.layout.Spacer(height=30),
            hhd,hhdt,
            '1-Vegan,2-Veget.,3-Pesc.,4-Omniv.,5-Paleo,6-Keto',
            hh_text6,hh_text5,
            pn.layout.Spacer(height=30),            
            styles={'background': 'black'}
        ),
        pn.layout.Spacer(width=50),        
            pn.Column(
            '## Your Results',
            fig,
            styles={'background': 'black'}
        ),
        pn.layout.Spacer(width=50),        
        dynamic = True,styles={'background': 'black'},
        name = 'Household'        
    ),
    pn.Row(
        pn.layout.Spacer(width=50),        
        pn.Column(
            '## Your Results: Power',
            fig,
            styles={'background': 'black'}
        ),
        pn.layout.Spacer(width=50),        
        pn.Column(
            '## Your Results: Emissions',
            fig2,
            styles={'background': 'black'}
        ),
        pn.Column(
            '## Your Results: 3rd Factor',
            #fig3,
            styles={'background': 'black'}
        ),
        pn.layout.Spacer(width=50),        
        dynamic = True,styles={'background': 'black'},
        name = 'Results'        
    )
).servable

# TODO Your Local Power Grid chart
# TODO Your CO2 Emissions chart - done!
# TODO public transportation & air travel - done!
# TODO household clean energy (solar, geothermal) input & calculator
# TODO tabular summary page, with download?
# TODO fix the ZIP lookup for 43017 and others - done!
# TODO fix the vehicle fuel calculations - done!
# TODO convert to simple Python 
# TODO figure out hosting
