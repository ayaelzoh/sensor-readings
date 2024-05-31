import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from rq import Queue

# Replace with your queue implementation (e.g., Redis Queue)
q = Queue()

# ... (rest of your data fetching and processing logic from the original code)

def update_data():
  # Fetch data from Google Sheet
  df = fetch_data()

  # Push data to the queue
  q.enqueue(df.to_json())

if __name__ == "__main__":
  # Schedule data update every 5 seconds (adjust as needed)
  while True:
    update_data()
    time.sleep(5)
