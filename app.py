import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import time

# Add an image to the top of your Streamlit app
st.image('/Users/juanarizti/Desktop/Herbie/mqdc-idyllias-logo.png', use_column_width=True)

# Add a title to your Streamlit app
st.title('Herbie Sensor Readings')
st.subheader('Welcome to the sensor data dashboard')
st.write('Here you can see the latest sensor readings from the Herbie project.')

# Path to your JSON key file
SERVICE_ACCOUNT_FILE = '/Users/juanarizti/Desktop/Herbie/herbie_key.json'

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
def fetch_data():
    # Fetch all records from the sheet
    data = sheet.get_all_records()

    # Convert the records to a pandas DataFrame
    df = pd.DataFrame(data)

    # Ensure 'TimeString' is datetime and set as index
    df['TimeString'] = pd.to_datetime(df['TimeString'])
    df.set_index('TimeString', inplace=True)

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
    fig = px.line(df, x=df.index, y=['Light', 'Water', 'Moist', 'Temp', 'Humid'],
                  labels={'value': 'Value', 'index': 'DateTime'},
                  title=title,
                  color_discrete_map={'Light': 'blue', 'Water': 'green', 'Moist': 'red', 'Temp': 'orange', 'Humid': 'purple'},
                  line_dash_sequence=['solid']*5)  # Ensure solid lines for all sensors
    return fig

# Create placeholders for line charts
realtime_placeholder = st.empty()
hourly_placeholder = st.empty()

# Continuous loop to update line charts
while True:
    # Fetch real-time data
    df = fetch_data()

    # Create real-time line chart
    fig_realtime = create_line_chart(df.tail(2000), 'Real-Time Sensor Readings (Last 2000 Timestamps)')
    realtime_placeholder.plotly_chart(fig_realtime, use_container_width=True)

    # Resample data to hourly intervals and calculate the mean value
    df_hourly_avg = df.resample('H').mean()

    # Create hourly line chart
    fig_hourly = create_line_chart(df_hourly_avg, 'Average Hourly Sensor Readings')
    hourly_placeholder.plotly_chart(fig_hourly, use_container_width=True)

    # Pause briefly before fetching new data and updating the charts
    time.sleep(5)  # Adjust the pause duration as needed