# Climate Dashboard prototype notebook

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

import Climate_fx as cf

hvplot.extension('bokeh')

pn.extension(design='bootstrap')

# establish design parameters
intwidth = 100
textcolor = 'black'
backcolor1 = 'darkgrey'
backcolor2 = 'lightgrey'

# widget to input ZIP code and get coefficient
ZIP_entry = pn.widgets.IntInput(name="ZIP Code",
                                value=43017,width=intwidth,
                                styles={'color':textcolor})

##### Section 1 - Vehicles #################################

# widgets to specify vehicle #1 usage
v1t = pn.widgets.Select(name='Vehicle #1 Type',options=cf.veh_list,value='SUV-Compact-ICE')
v1m = pn.widgets.IntSlider(name="Annual Mileage",value=0,start=0,end=30000,step=1000)
v1h = pn.widgets.IntSlider(name='% Highway Driving',value=50,start=0,end=100,step=5)
# detect vehicle fuel type, calculate energy usage and CO2
v1f = pn.bind(cf.get_veh_type,cf.veh_data,v1t)
v1_isev = pn.bind(cf.check_ev,v1t)
v1g = pn.bind(cf.get_veh_usage,cf.veh_data,v1t,v1m,v1h,
                retval='gal',timeconv=cf.year_to_week)  # direct calc yearly gas usage gal
v1k = pn.bind(cf.get_veh_usage,cf.veh_data,v1t,v1m,v1h,
                retval='kwh',timeconv=cf.year_to_week)  # direct calc yearly kwh
v1c = pn.bind(cf.get_veh_usage,cf.veh_data,v1t,v1m,v1h,
                retval='co2',zip=ZIP_entry,timeconv=cf.year_to_week)   # grid emissions co2

# create pretty text widgets to show the vehicle coefficients
fuel_text1a = pn.widgets.StaticText(name = "Vehicle weekly fuel (gal)",value=v1g)
fuel_text1b = pn.widgets.StaticText(name = "Vehicle weekly energy (kWh)",value=v1k)
co2_text1 = pn.widgets.StaticText(name = "Indirect weekly emissions (kg CO2)",value=v1c)    

# widgets to specify vehicle #2 usage
v2t = pn.widgets.Select(name='Vehicle #2 Type',options=cf.veh_list,value='SUV-Compact-ICE')
v2m = pn.widgets.IntSlider(name="Annual Mileage",value=0,start=0,end=30000,step=1000)
v2h = pn.widgets.IntSlider(name='% Highway Driving',value=50,start=0,end=100,step=5)

# widgets to specify vehicle #3 usage
v3t = pn.widgets.Select(name='Vehicle #3 Type',options=cf.veh_list,value='SUV-Compact-ICE')
v3m = pn.widgets.IntSlider(name="Annual Mileage",value=0,start=0,end=30000,step=1000)
v3h = pn.widgets.IntSlider(name='% Highway Driving',value=50,start=0,end=100,step=5)

# widgets to specify vehicle #4 usage
v4t = pn.widgets.Select(name='Vehicle #4 Type',options=cf.veh_list,value='SUV-Compact-ICE')
v4m = pn.widgets.IntSlider(name="Annual Mileage",value=0,start=0,end=30000,step=1000)
v4h = pn.widgets.IntSlider(name='% Highway Driving',value=50,start=0,end=100,step=5)

# widgets to specify public transportation usage
ptm = pn.widgets.IntSlider(name="Bus/Train Annual Rider Mileage",value=0,start=0,end=20000,step=500)
ptc = pn.bind(cf.convert,ptm,cf.pubtrans_co2_coeff,cf.year_to_week)      # direct emissions co2
ptk1 = pn.bind(cf.convert,ptm,1/cf.pubtrans_fe,cf.year_to_week)          # fuel consumption, gal
ptk2 = pn.bind(cf.convert,ptk1,cf.petrol_kwh_coeff)                   # equivalent kwh
pt_text1a = pn.widgets.StaticText(name = "Public Transit weekly fuel (gal)",value=ptk1)
pt_text1b = pn.widgets.StaticText(name = "Public Transit weekly energy (kWh)",value=ptk2)
pt_text2 = pn.widgets.StaticText(name = "Public Transit weekly emissions (kg CO2)",value=ptc)

# widgets to specify air travel usage
ath = pn.widgets.IntSlider(name="Air Travel Annual Flight Hours",value=0,start=0,end=200,step=10)
atc = pn.bind(cf.convert,ath,cf.air_co2_coeff,cf.year_to_week)      # direct emissions co2
atk1 = pn.bind(cf.convert,ath,cf.air_fe_rate,cf.year_to_week)          # fuel consumption, gal
atk2 = pn.bind(cf.convert,atk1,cf.petrol_kwh_coeff)                   # equivalent kwh
at_text1a = pn.widgets.StaticText(name = "Air Travel weekly fuel (gal)",value=atk1)
at_text1b = pn.widgets.StaticText(name = "Air Travel weekly energy (kWh)",value=atk2)
at_text2 = pn.widgets.StaticText(name = "Air Travel weekly emissions (kg CO2)",value=atc) 

##### Section 2 - Household #################################

# bind the coefficient output to the lookup function and input
ZIP_coeff = pn.bind(cf.coeff_lookup,cf.grid_coeff_data,ZIP_entry)
# create a pretty text widget to show the grid coefficient
ZIP_text = pn.widgets.StaticText(name = "Local kg-CO2/kWh Coefficient",value=ZIP_coeff)

# widget to enter monthly energy usage
hhe = pn.widgets.IntSlider(name="Monthly Home Electric Usage (kWh)",value=0,start=0,end=2000,step=50)
# calculate usage
hhelectric_co2 = pn.bind(cf.convert,hhe,ZIP_coeff,12/52)
hhelectric_kwh = pn.bind(cf.convert,hhe,12/52)

# widget to enter monthly natural gas usage
hhn = pn.widgets.IntSlider(name="Monthly Home Natural Gas Usage (ccf)",value=0,start=0,end=200,step=5)
# calculate usage
hhnatgas_co2 = pn.bind(cf.convert,hhn,cf.natgas_co2_coeff,12/52)
hhnatgas_kwh = pn.bind(cf.convert,hhn,cf.natgas_kwh_coeff,12/52)

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
# then multiply by the num of calories and convert from daily to weekhly
hhdiet_co2_coeff = pn.bind(cf.list_lookup,cf.diet_co2_eq,hhdt)
hhdiet_prod_coeff = pn.bind(cf.list_lookup,cf.diet_prod_mult,hhdt)
hhdiet_co2 = pn.bind(cf.convert,hhd,hhdiet_co2_coeff,0.001*7)
hhdiet_kwh = pn.bind(cf.convert,hhd,hhdiet_prod_coeff,cf.diet_kcal_to_kwh*7)

# create pretty text widgets to show the vehicle coefficients
hh_text5 = pn.widgets.StaticText(name = "HH weekly diet (kg CO2)",value=hhdiet_co2)
hh_text6 = pn.widgets.StaticText(name = "HH weekly diet (kWh)",value=hhdiet_kwh)

# create a plot of the total energy consumption
fig = pn.bind(cf.plot_usage_2,
            v1t,v1h,v1m,
            v2t,v2h,v2m,
            v3t,v3h,v3m,
            v4t,v4h,v4m,
            ptm,ath,
            hhe,hhn,hh_pop,
            hhd,hhdt
            )

# create a plot of the total energy consumption
fig2 = pn.bind(cf.plot_co2,
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
        pn.layout.Spacer(width=50),        
        dynamic = True,styles={'background': 'black'},
        name = 'Results'        
    )
).servable()