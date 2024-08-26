import time
import os
import json
import streamlit as st
import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# -------------------- CONFIGURATION --------------------

# Define the scope and credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Load the credentials from Streamlit secrets
credentials_info = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=['https://www.googleapis.com/auth/spreadsheets'])

# Build the service
service = build('sheets', 'v4', credentials=credentials)

# Spreadsheet ID and range configuration
SPREADSHEET_ID = '1YrdM-TmiQzVnW_eg9bGlXojJWhY8bUHMrOVKl3k55Jw'
RANGE_NAME = 'sheet1!A2:F'  # Update the range as needed


def get_data_from_sheet():
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME
    ).execute()
    values = result.get('values', [])
    if not values:
        st.warning('No data found.')
        return pd.DataFrame()
    else:
        df = pd.DataFrame(
            values,
            columns=['ID', 'Vehicle Type', 'Direction', 'Speed (km/h)', 'Current Time', 'Congestion Level']
        )
        return df


# -------------------- STREAMLIT APP --------------------

# Set page configuration
st.set_page_config(
    page_title='Traffic Dashboard',
    page_icon='🚗',
    layout='wide'
)

# Dashboard title
st.markdown("""
    <h1 style='text-align: center; margin-bottom: 50px;'>
        TARABA TRANSPORT DT
    </h1>
""", unsafe_allow_html=True)

# Sidebar filters
st.sidebar.header("Filters")
start_button = st.sidebar.checkbox("Start Real-Time Update")

# Placeholder for error messages
error_placeholder = st.empty()

# Initialize data
data = get_data_from_sheet()

if data.empty:
    st.stop()

# Extract unique values for filters
vehicle_types = ['All'] + sorted(data["Vehicle Type"].unique())
directions = ['All'] + sorted(data["Direction"].unique())

# Sidebar selectboxes for filtering
selected_vehicle_type = st.sidebar.selectbox(
    "Select Vehicle Type",
    vehicle_types,
    key='vehicle_type_selectbox'
)

selected_direction = st.sidebar.selectbox(
    "Select Direction",
    directions,
    key='direction_selectbox'
)

# Initialize placeholders for KPIs and charts
kpi_placeholder = st.empty()
chart_placeholder = st.empty()
data_table_placeholder = st.empty()

# Main update loop
if start_button:
    while True:
        try:
            # Fetch and process data
            data = get_data_from_sheet()

            if data.empty:
                error_placeholder.error("No data available to display.")
                time.sleep(1)
                continue
            else:
                error_placeholder.empty()

            # Data type conversions
            data["Speed (km/h)"] = pd.to_numeric(data["Speed (km/h)"], errors='coerce')
            data['Current Time'] = pd.to_datetime(data['Current Time'], errors='coerce')

            # Apply filters
            filtered_data = data.copy()
            if selected_vehicle_type != 'All':
                filtered_data = filtered_data[filtered_data["Vehicle Type"] == selected_vehicle_type]
            if selected_direction != 'All':
                filtered_data = filtered_data[filtered_data["Direction"] == selected_direction]

            if filtered_data.empty:
                error_placeholder.warning("No data matches the selected filters.")
                time.sleep(1)
                continue
            else:
                error_placeholder.empty()

            # Calculate KPIs
            average_speed = filtered_data["Speed (km/h)"].mean()
            total_vehicle_count = len(filtered_data)
            distance = 1.47  # km
            average_travel_time = (distance / average_speed) * 60 if average_speed else None
            daily_traffic = filtered_data.groupby(filtered_data['Current Time'].dt.date).size().reset_index(
                name='Count')
            average_daily_traffic = daily_traffic['Count'].mean() if not daily_traffic.empty else 0

            # Update KPIs
            with kpi_placeholder.container():
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)

                kpi1.metric(
                    label="Average Speed (km/h)",
                    value=f"{average_speed:.2f}" if average_speed else "N/A"
                )

                kpi2.metric(
                    label="Average Travel Time (min)",
                    value=f"{average_travel_time:.2f}" if average_travel_time else "N/A"
                )

                kpi3.metric(
                    label="Segment Distance (km)",
                    value=f"{distance:.2f}"
                )

                kpi4.metric(
                    label="Total Vehicle Count",
                    value=f"{total_vehicle_count}"
                )

            # Update charts
            with chart_placeholder.container():
                chart_col1, chart_col2, chart_col3 = st.columns(3)

                with chart_col1:
                    fig1 = px.histogram(
                        filtered_data,
                        x="Direction",
                        title="Distribution of Directions",
                        color_discrete_sequence=['#636EFA']
                    )
                    st.plotly_chart(fig1, use_container_width=True)

                with chart_col2:
                    fig2 = px.histogram(
                        filtered_data,
                        x="Vehicle Type",
                        title="Distribution of Vehicle Types",
                        color_discrete_sequence=['#EF553B']
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                with chart_col3:
                    if not daily_traffic.empty:
                        fig3 = go.Figure()
                        fig3.add_trace(go.Bar(
                            x=daily_traffic['Current Time'],
                            y=daily_traffic['Count'],
                            name='Daily Traffic',
                            marker_color='green'
                        ))
                        fig3.add_trace(go.Scatter(
                            x=daily_traffic['Current Time'],
                            y=[average_daily_traffic] * len(daily_traffic),
                            mode='lines',
                            name='Average Daily Traffic',
                            line=dict(color='red', dash='dash')
                        ))
                        fig3.update_layout(
                            title='Daily Traffic Counts',
                            xaxis_title='Date',
                            yaxis_title='Number of Vehicles'
                        )
                        st.plotly_chart(fig3, use_container_width=True)
                    else:
                        st.info("Not enough data for Daily Traffic chart.")

            # Update data table
            with data_table_placeholder.container():
                st.dataframe(filtered_data)

            # Wait for 1 second before next update
            time.sleep(1)

        except Exception as e:
            error_placeholder.error(f"An error occurred: {e}")
            time.sleep(5)
else:
    st.info("Real-Time Update is stopped. Check the box in the sidebar to start.")
