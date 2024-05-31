import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import time

# Add an image to the top of Streamlit app
st.image('mqdc-idyllias-logo.png', use_column_width=True)

# Add a title to Streamlit app
st.title('Herbie Sensor Readings')
st.subheader('Welcome to the sensor data dashboard')
st.write('Here you can see the latest sensor readings from the Herbie project.')

# Path to JSON key file
SERVICE_ACCOUNT_FILE = 'herbie_key.json'

# Define the scope
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Authenticate with the JSON key file
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# Open the Google Sheet by name
spreadsheet = client.open("HerbieData")

# Select the specific sheet within the Google Sheet
sheet = spreadsheet.worksheet("Forestias-0001")

# Function to fetch data from Google Sheet and preprocess it
@st.cache_data(ttl=60)  # Cache the data for 60 seconds to prevent continuous repetition
def fetch_data():
    # Fetch all records from the sheet
    data = sheet.get_all_records()

    # Convert the records to a pandas DataFrame
    df = pd.DataFrame(data)

    df.rename(columns={'TimeString': 'Time', 'Temp': 'Temperature', 'Moist': 'Soil Moisture', 'Humid': 'Humidity'}, inplace=True)

    # Ensure 'TimeString' is datetime and set as index
    df['Time'] = pd.to_datetime(df['Time'])
    df.set_index('Time', inplace=True)

    # Drop unwanted columns
    unwanted_columns = ['Herbie_ID']
    df.drop(columns=unwanted_columns, inplace=True, errors='ignore')

    # Select data starting from index 17302 (if exists)
    if len(df) > 17302:
        df = df.iloc[17302:]

    # Fill NaN values with 0
    df = df.fillna(0)

    # Convert all columns to numeric
    df = df.apply(pd.to_numeric, errors='coerce')

    return df

# Function to create line chart
def create_line_chart(df, title):
    fig = px.line(df, x=df.index, y=['Light', 'Water', 'Soil Moisture', 'Temperature', 'Humidity'],
                  labels={'value': 'Value', 'index': 'Time'},
                  title=title,
                  color_discrete_map={'Light': 'blue', 'Water': 'green', 'Soil Moisture': 'red', 'Temperature': 'orange', 'Humidity': 'purple'},
                  line_dash_sequence=['solid']*5)  # Ensure solid lines for all sensors
    return fig

# Create placeholders for metrics and line charts
metric_columns = st.columns(5)
realtime_placeholder = st.empty()
hourly_placeholder = st.empty()

# Function to update metrics
def update_metrics(df, differences):
    metrics = ['Light', 'Water', 'Soil Moisture', 'Temperature', 'Humidity']
    for i, col in enumerate(metrics):
        if col in df.columns:
            current_value = df[col].iloc[-1]
            delta_value = differences[col] if not differences.empty else 0
            metric_columns[i].metric(col, value=current_value, delta=delta_value)

# Continuous loop to update metrics and line charts
while True:
    # Fetch real-time data
    df = fetch_data()

    if not df.empty:
        # Calculate differences between previous and current data
        differences = df.diff().iloc[-1]

        # Update metrics
        update_metrics(df, differences)

        # Create real-time line chart
        fig_realtime = create_line_chart(df.tail(2000), 'Real-Time Sensor Readings')
        realtime_placeholder.plotly_chart(fig_realtime, use_container_width=True)

        # Resample data to hourly intervals and calculate the mean value
        df_hourly_avg = df.resample('H').mean()

        # Create hourly line chart
        fig_hourly = create_line_chart(df_hourly_avg, 'Average Hourly Sensor Readings')
        hourly_placeholder.plotly_chart(fig_hourly, use_container_width=True)

    # Pause briefly before fetching new data and updating the charts
    time.sleep(60)  # Adjust the pause duration as needed
