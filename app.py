# -*- coding: utf-8 -*-


# !pip install gspread
# import gspread

import os
credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
if not credentials_json:
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable is not set")

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_json


import pytz
import json
import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
from datetime import datetime

def get_fresh_cookies():
    # This URL will be the one that sets the cookies initially after login or first access.
    url = 'https://www.nseindia.com'
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    response = requests.get(url, headers=headers)
    cookie_jar = response.cookies
    cookie = "; ".join([f"{cookie.name}={cookie.value}" for cookie in cookie_jar])

    # Print the cookie string to see the formatted output
    print("Formatted Cookie String:", cookie)

    return cookie  # Returning the cookie jar for further usage

def make_authenticated_request(url, cookies):
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    # Ensure to pass cookies as the cookie jar object
    response = requests.get(url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch data with status code:", response.status_code)
        return None  # Handle errors appropriately


cookie = get_fresh_cookies()

def authenticate_gspread(creds):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_json = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'), strict = False)
    creds = Credentials.from_service_account_info(creds_json ,scopes=scope)
    client = gspread.authorize(creds)
    return client



def fetch_and_update_sheet(symbols, sheet_name, creds):
    client = authenticate_gspread(creds)
    sheet = client.open(sheet_name).sheet1
    sheet_data = []

    if sheet.row_count < 1:
        headers = ["Time", "Symbol", "Delivery to Traded Quantity", "Quantity Traded", "Delivery Quantity"]
        sheet.append_row(headers)  # Append the headers to the sheet

    # Set the timezone to IST
    ist = pytz.timezone('Asia/Kolkata')

    for symbol in symbols:
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}&section=trade_info"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Referer': f'https://www.nseindia.com/get-quotes/equity?symbol={symbol}',
            'scheme': 'https',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-AS,en-US;q=0.9,en;q=0.8,ta;q=0.7',
            'Cookie': cookie
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(response.text)  # Add this to debug the raw output of the API response
        else:
            print("Failed to fetch data:", response.status_code)
            continue

        if data.get('securityWiseDP'):
            security_wise_dp = data['securityWiseDP']
            current_time_ist = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
            quantityTraded = security_wise_dp.get('quantityTraded', 0)
            deliveryQuantity = security_wise_dp.get('deliveryQuantity', 0)
            deliveryToTradedQuantity = security_wise_dp.get('deliveryToTradedQuantity', 0)

            row = [current_time_ist, symbol, deliveryToTradedQuantity, quantityTraded, deliveryQuantity]
            sheet.append_row(row)  # Append the data row to the sheet
            sheet_data.append(row)
    return sheet_data

# Usage example
symbols = ['HDFCBANK', 'RELIANCE', 'TCS']
sheet_name = 'sheets'  # Ensure this matches exactly with your Google Sheets name

# Fetch data and update sheet
sheet_data = fetch_and_update_sheet(symbols, sheet_name)

# Print the sheet data
for row in sheet_data:
    print(row)
