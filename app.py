import requests
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
import streamlit as st
from streamlit_folium import st_folium

# Load API Key from .env file (Optional, recommended for security)
import os
from dotenv import load_dotenv
load_dotenv()

# Get your API key from the .env file or use hardcoded one for testing
api_key = os.getenv('OPENCHARGEMAP_API_KEY')

# Open Charge Map API URL
api_url = "https://api.openchargemap.io/v3/poi/"

# Parameters for the API request
params = {
    'output': 'json',
    'countrycode': 'DE',  # Germany
    'maxresults': 500,  # Limit to 500 results
    'compact': True,  # Compact format for the response
    'verbose': False,  # Detailed output
    'key': api_key  # Add your API key here
}

# Fetch data from Open Charge Map API
try:
    response = requests.get(api_url, params=params)
    response.raise_for_status()  # Raise an error if the response status is not OK

    if response.text.strip():  # Check if the response is not empty
        data = response.json()

    else:
        st.write("No data available or empty response received!")

except requests.exceptions.RequestException as e:
    st.error(f"Error fetching data: {e}")

# Extract relevant information into a DataFrame
stations = []
for item in data:
    station = {
        'Name': item.get('AddressInfo', {}).get('Title', 'N/A'),
        'Latitude': item.get('AddressInfo', {}).get('Latitude', None),
        'Longitude': item.get('AddressInfo', {}).get('Longitude', None),
        'Address': item.get('AddressInfo', {}).get('AddressLine1', 'N/A'),
        'Town': item.get('AddressInfo', {}).get('Town', 'N/A'),
        'State': item.get('AddressInfo', {}).get('StateOrProvince', 'N/A'),
        'Postcode': item.get('AddressInfo', {}).get('Postcode', 'N/A'),
        'Operator': item.get('OperatorInfo', {}).get('Title', 'N/A'),
        'UsageCost': item.get('UsageCost', 'N/A')
    }
    stations.append(station)

df = pd.DataFrame(stations)

# Convert DataFrame to GeoDataFrame
gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df['Longitude'], df['Latitude']),
    crs="EPSG:4326"  # WGS84 coordinate system
)

# Create a list of unique states for the dropdown menu
states = sorted(df['State'].unique())
selected_state = st.sidebar.selectbox('Select a State', ['All'] + states)

# Filter the DataFrame based on the selected state
if selected_state != 'All':
    filtered_gdf = gdf[gdf['State'] == selected_state]
else:
    filtered_gdf = gdf

# Set dynamic title based on selected state
if selected_state == 'All':
    map_title = 'E-Charging Stations in Germany'
else:
    map_title = f'E-Charging Stations in {selected_state}, Germany'

# Display the dynamic title above the map
st.title(map_title)  # This is where the dynamic title is set in Streamlit

# Create a Folium map centered on Germany
map_center = [51.1657, 10.4515]  # Center of Germany
m = folium.Map(location=map_center, zoom_start=6, tiles='CartoDB dark_matter')

# Add marker clusters
charging_cluster = MarkerCluster(name='E-Charging Stations').add_to(m)

# Add e-charging stations to the map (filtered by state)
for idx, row in filtered_gdf.iterrows():
    popup_content = f"""
    <strong>Station:</strong> {row['Name']}<br>
    <strong>Operator:</strong> {row['Operator']}<br>
    <strong>Address:</strong> {row['Address']}, {row['Town']}, {row['State']}, {row['Postcode']}<br>
    <strong>Usage Cost:</strong> {row['UsageCost']}
    """
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        icon=folium.Icon(color='green', icon='plug'),
        popup=popup_content
    ).add_to(charging_cluster)

# Add layer control
folium.LayerControl(collapsed=False).add_to(m)

# Display the map in Streamlit
st_folium(m, width=700)