import streamlit as st
import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = r'C:\Users\Joshua Odeleye\Documents\streamlit-Traffic\credentials.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('sheets', 'v4', credentials=credentials)
SPREADSHEET_ID = '1YrdM-TmiQzVnW_eg9bGlXojJWhY8bUHMrOVKl3k55Jw'
RANGE_NAME = 'sheet1!A2:F'  # Update the range as needed

def get_data_from_sheet():
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    if not values:
        st.write('No data found.')
        return pd.DataFrame()
    else:
        df = pd.DataFrame(values, columns=['ID', 'Vehicle Type', 'Direction', 'Speed (km/h)', 'Time', 'Congestion Level'])
        return df


st.set_page_config(
    page_title = 'Traffic Dashboard',
    page_icon = '✅',
    layout = 'wide'
)

# dashboard title
st.markdown("""
    <style>
    .title {
        text-align: center;
        font-size: 2em;
        font-weight: bold;
         margin-top: -80px;
    }
    </style>
""", unsafe_allow_html=True)

# HTML to render the title
st.markdown('<h1 class="title">Real-Time Traffic Information </h1>', unsafe_allow_html=True)

# Get data from Google Sheets
data = get_data_from_sheet()

if not data.empty:
    # Extract unique vehicle types and directions for the select boxes
    vehicle_types = ['All'] + data["Vehicle Type"].unique().tolist()
    directions = ['All'] + data["Direction"].unique().tolist()

    # Selectbox for vehicle type and direction
    selected_vehicle_type = st.sidebar.selectbox("Select Vehicle Type", vehicle_types)
    selected_direction = st.sidebar.selectbox("Select Direction", directions)

    # Filter the data based on the selected vehicle type and direction
    if selected_vehicle_type != 'All':
        data = data[data["Vehicle Type"] == selected_vehicle_type]
    if selected_direction != 'All':
        data = data[data["Direction"] == selected_direction]

    # Display the filtered data
    #st.write(f"Filtered Data for Vehicle Type: {selected_vehicle_type} and Direction: {selected_direction}")
    #st.dataframe(data)
#else:
    #st.write("No data to display.")

placeholder = st.empty()


# Calculate Average Speed
average_speed = data["Speed (km/h)"].astype(float).mean()

# Calculate Total Vehicle Type Count
total_vehicle_count = data["Vehicle Type"].count()

# Calculate Total Counts for Each Vehicle Type
total_car_count = data[data["Vehicle Type"].str.lower() == "car"].shape[0]
total_bus_count = data[data["Vehicle Type"].str.lower() == "bus"].shape[0]
total_motorcycle_count = data[data["Vehicle Type"].str.lower() == "motorcycle"].shape[0]

# Given distance in kilometers
distance = 1.47  # km

# Calculate Average Travel Time (time = distance / speed)
average_travel_time = distance / average_speed * 60  # travel time in minutes

with placeholder.container():
    # create three columns
    st.markdown("""
        <style>
        .metric-container {
            text-align: center;
            border: 2px solid #e6e6e6;
            border-radius: 10px;
            padding: 12px;
            padding-left: 0.1rem;
            padding-right: 0.1rem;
            margin: 8px;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
        }
        .metric-label {
            font-size: 1.2em;
            color: red;
        }
        .metric-button {
            margin-top: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Create columns for KPIs
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    # Display metrics in columns with additional styling
    with kpi1:
        st.markdown(
            '<div class="metric-container"><div class="metric-value">' + f"{average_speed:.2f} km/h" + '</div><div class="metric-label">Average Speed</div></div>',
            unsafe_allow_html=True)

    with kpi2:
        st.markdown(
            '<div class="metric-container"><div class="metric-value">' + f"{average_travel_time:.2f} min" + '</div><div class="metric-label">Average Travel Time</div></div>',
            unsafe_allow_html=True)

    with kpi3:
        st.markdown(
            '<div class="metric-container"><div class="metric-value">' + f"{distance:.4f} km" + '</div><div class="metric-label">Segment Distance</div></div>',
            unsafe_allow_html=True)

    with kpi4:
        st.markdown(
            '<div class="metric-container"><div class="metric-value">' + f"{total_vehicle_count}" + '</div><div class="metric-label">Total Vehicle Count</div></div>',
            unsafe_allow_html=True)

    fig_col1, fig_col2, fig_col3 = st.columns(3)

    # Create histogram for "Direction" column
    with fig_col1:
        st.markdown(" ")
        fig1 = px.histogram(data, x="Direction", title="Distribution of Directions")
        st.plotly_chart(fig1, use_container_width=True)

    # Create histogram for "Vehicle Type" column
    with fig_col2:
        st.markdown(" ")
        fig2 = px.histogram(data, x="Vehicle Type", title="Distribution of Vehicle Types")
        st.plotly_chart(fig2, use_container_width=True)

    # Display the DataFrame for the fetched data
    with fig_col3:
        st.markdown("## Traffic Data")
        st.dataframe(data)