#Import the libraries
import streamlit as st
import geopandas as gpd
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mapclassify as mc
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import mplcursors
import altair as alt
from PIL import Image
import matplotlib.patheffects as path_effects
from shapely.geometry import Point
from adjustText import adjust_text
##############################
# Load data
data=pd.read_csv('https://raw.githubusercontent.com/fayam1/Sudat-DTM-Analysis/main/Data/Sudan_IDPs_admin1_final.csv')
# Load the Sudan admin1 shapefile
shapefile_path = 'https://raw.githubusercontent.com/fayam1/Sudat-DTM-Analysis/main/Data/sudan_adm1.shp'

sudan_gdf = gpd.read_file(shapefile_path)
#Remove the spaces from columns names
data.columns = data.columns.str.strip()
st.set_page_config(layout="wide")
st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)
image = Image.open('iom_logo.jpg')

col0, col1 = st.columns([0.1,0.9])
with col0:
 st.image(image,width=300)
html_title = """
    <style>
    .title-test {
    font-weight:bold;
    padding:20px;
    border-radius:20px;
    }
    </style>
    <center><h1 class="title-test">Sudan IDPs DTM  Dashboard</h1></center>"""
with col1:
    st.markdown(html_title, unsafe_allow_html=True)  

col2,col3,col4=st.columns([0.3,1.1,1],gap='medium')

with col2:
  
 # Get unique years and months
  year_list = list(data.Year.unique())[::-1]
  month_list = list(data.Month.unique())[::-1]

# Create the UI elements
  selected_year = st.selectbox('Select a year',year_list )
  
  filtered_months = [month for month in month_list if data[(data.Year == selected_year) & (data.Month == month)].any(axis=None)]
  selected_month = st.selectbox('Select a month', filtered_months)

df_selected_year =data[data.Year == selected_year]
df_selected_year_month = data[(data['Year'] == selected_year) & (data['Month'] == selected_month)]
total_idps_by_State_Of_Origin_selected_year = df_selected_year.groupby(['State_origin_Code','State_Of_Origin','Year','Month']).agg({
'IDPs_by_State_Of_Origin': 'sum'    
}).reset_index()

# Sort by State_origin_Code and Month
total_idps_by_State_Of_Origin_selected_year = total_idps_by_State_Of_Origin_selected_year.sort_values(by=['State_origin_Code', 'Month'])
total_idps_by_State_Of_Origin_selected_month = df_selected_year_month.groupby(['State_origin_Code','State_Of_Origin','Year','Month']).agg({
'IDPs_by_State_Of_Origin': 'sum'    
}).reset_index()
# Calculate the difference with the previous month
total_idps_by_State_Of_Origin_selected_year['IDPs_difference'] = total_idps_by_State_Of_Origin_selected_year.groupby('State_origin_Code')['IDPs_by_State_Of_Origin'].diff().fillna(0)
total_idps_by_State_Of_Origin_selected_year['IDPs_difference_absolute'] = total_idps_by_State_Of_Origin_selected_year['IDPs_difference'].abs()

merged_gdf = sudan_gdf.merge(total_idps_by_State_Of_Origin_selected_month , how='left', left_on='ADM1_PCODE', right_on='State_origin_Code')
########################
# Plots 
#Map      
def format_number(x, pos):
    """Format the color bar labels."""
    if x >= 1_000_000:
        return f'{x / 1_000_000:.1f}M'
    elif x >= 1_000:
        return f'{x / 1_000:.1f}K'
    else:
        return str(int(x))

def create_choropleth_map(merged_gdf, column, color_theme, year, month, figsize=(15, 10), fig=None):
    # Perform Natural Breaks (Jenks) classification
    classifier = mc.NaturalBreaks(merged_gdf[column].fillna(0), k=5)
    merged_gdf['jenks_bins'] = classifier.yb

    # Create the colormap
    cmap = plt.get_cmap(color_theme)
    norm = mcolors.BoundaryNorm(boundaries=classifier.bins, ncolors=cmap.N)

    # Set the background color to black
    fig, ax = plt.subplots(1, 1, figsize=figsize, facecolor='black')

    # Plot the graduated color map
    merged_gdf[merged_gdf[column].notna()].plot(column='jenks_bins', cmap=cmap, linewidth=1.5, ax=ax, edgecolor='0.6', legend=False)

    # Plot the states without values as no fill
    merged_gdf[merged_gdf[column].isna()].plot(color='none', edgecolor='0.8', linewidth=1.1, ax=ax)

    # Add a color bar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # Only needed for matplotlib < 3.1
    cbar = fig.colorbar(sm, ax=ax, orientation='vertical', fraction=0.02, pad=0.04)
    # cbar.set_label('IDPs by State', fontsize=12, color='white')

    # Add ticks and labels to the color bar
    cbar.set_ticks(classifier.bins)
    cbar.ax.set_yticklabels([format_number(x, None) for x in classifier.bins])
    cbar.ax.tick_params(labelsize=14, colors='white')

    # Add a dynamic title based on the selected year and month
    ax.set_title(f'IDPs distribution by State Of Origin in Sudan as of {month}-{year}', fontsize=22,fontweight='bold', color='white')

    # Turn off the axis
    ax.axis('off')

    # Add State names to the map with gray outline and white outline
    texts = []
    for x, y, label in zip(merged_gdf.geometry.centroid.x, merged_gdf.geometry.centroid.y, merged_gdf['ADM1_EN']):
        txt = ax.text(x, y, label, fontsize=12, fontweight='bold', ha='center', va='center', color='white')
        txt.set_path_effects([
            path_effects.Stroke(linewidth=1.6, foreground='black'),
            path_effects.Stroke(linewidth=0.3, foreground='white'),
            path_effects.Normal()
        ])
        texts.append(txt)

    # Adjust text positions to avoid overlaps
    adjust_text(texts, arrowprops=dict(arrowstyle="-", color='white', lw=0.5), ax=ax)

    return fig

figsize=(15,10)    
fig=create_choropleth_map(merged_gdf, 'IDPs_by_State_Of_Origin', 'YlOrRd',selected_year,selected_month,figsize = figsize)

with col3:
 
 st.pyplot(fig, use_container_width=True)

 ###############
 # Calculate the difference with the previous month
total_idps_by_State_Of_Origin_selected_year['IDPs_difference'] = total_idps_by_State_Of_Origin_selected_year.groupby('State_origin_Code')['IDPs_by_State_Of_Origin'].diff().fillna(0)
total_idps_by_State_Of_Origin_selected_year['IDPs_difference_absolute'] = total_idps_by_State_Of_Origin_selected_year['IDPs_difference'].abs()
# Heatmap
def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme,selected_year):
    # Define the month order
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    tooltip=[
        alt.Tooltip('Month:O', title='Month'),
        alt.Tooltip('State_Of_Origin:N', title='State Of Origin'),
        alt.Tooltip('IDPs_by_State_Of_Origin:Q', title='IDPs by State Of Origin'),
        alt.Tooltip('IDPs_difference:Q', title='IDPs Change')]
    heatmap = alt.Chart(input_df).mark_rect().encode(
            y=alt.Y(f'{input_y}:O', sort=month_order, axis=alt.Axis(title="Month", titleFontSize=15, titlePadding=15, titleFontWeight='bold', labelAngle=0)),
            x=alt.X(f'{input_x}:O', axis=alt.Axis(title="", titleFontSize=15, titlePadding=15, titleFontWeight='bold')),
            color=alt.Color(f'{input_color}:Q',
                             legend=None,
                             scale=alt.Scale(scheme=input_color_theme)),
            stroke=alt.value('black'),
            strokeWidth=alt.value(0.25),
            tooltip=tooltip
        ).properties(
       title=f'IDPs Monthly Chenge by State Of Origin in : {selected_year}',
       width=1,
       height=300
#).configure_legend(
 #   orient='bottom', titleFontSize=16, labelFontSize=14, titlePadding=0
#).configure_axisX(
#    labelFontSize=14
).configure_axis(
    labelFontSize=15,
    titleFontSize=15
).configure_title(
    fontSize=16,
    anchor='middle',
    color='white'
    )
    return heatmap

#Second heatmap
#Preparing for calculating total IDPs by State of displacement

Total_idps_From_State_Origin_selected_month = df_selected_year_month.groupby(['State_Of_Origin','State_Of_Displacement']).agg({
'IDPs_by_State_Of_Origin': 'sum'    
}).reset_index()

Total_idps_From_State_Origin_selected_month=Total_idps_From_State_Origin_selected_month.rename(columns={'State_Of_Origin':'From State','State_Of_Displacement':'To State','IDPs_by_State_Of_Origin':'IDPs'})
##########################
#start second heatmap
# Create the heatmap using Altair
def create_heatmap(input_df, input_y, input_x, input_color, input_color_theme, selected_year, selected_month):
    # Filter the dataframe based on the selected year and month
    filtered_df = Total_idps_From_State_Origin_selected_month
    
    heatmap = alt.Chart(filtered_df).mark_rect().encode(
        x=alt.X(f'{input_x}:N', title='State Of Displacement'),
        y=alt.Y(f'{input_y}:N', title='State Of Origin'),
        color=alt.Color(f'{input_color}:Q', scale=alt.Scale(scheme=input_color_theme)),
        stroke=alt.value('black'),
        strokeWidth=alt.value(0.25),
        tooltip=[input_y, input_x, input_color]
    ).properties(
        title=f'IDPs Movement as {selected_month}-{selected_year}',
        width=600,
        height=400
    ).configure_title(
        fontSize=18,
        anchor='middle',
        color='white'
    ).configure_axis(
        labelFontSize=14,
        titleFontSize=14,
        labelColor='white',
        titleColor='white'
    ).configure_legend(
        labelFontSize=12,
        titleFontSize=14,
        labelColor='white',
        titleColor='white'
    )

    return heatmap


with col4:
 #st.markdown('#### IDPs Monthly Change')
#total_idps_by_State_Of_Origin_selected_year['Month']=filtered_months
 heatmap=make_heatmap(total_idps_by_State_Of_Origin_selected_year,'Month','State_Of_Origin','IDPs_by_State_Of_Origin', 'yelloworangered',selected_year )
 st.altair_chart(heatmap,use_container_width=True)
 heatmap1=create_heatmap(Total_idps_From_State_Origin_selected_month,'From State','To State','IDPs','yelloworangered',selected_year,selected_month)
 st.altair_chart(heatmap1,use_container_width=True)