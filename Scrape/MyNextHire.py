import time
import json
import re
import pandas as pd
import os.path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define constants for Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SAMPLE_SPREADSHEET_ID = "1YmpIPwk8il16xWaT7OlR9iMM0KsrSmjJ-OG29UeNoJU" 
SAMPLE_RANGE_NAME = "DarwinBox!A1"

# Company name mapping
COMPANY_NAMES = {
    "Swiggy": "swiggy",
}

all_jobs = []

options = Options()
options.headless = True

driver = webdriver.Chrome(options=options)

# API_URLs = [
#     "https://delhivery.darwinbox.in/ms/candidateapi/job?page=1&limit=50",
#     "https://godigit.darwinbox.in/ms/candidateapi/job?page=1&limit=50",
#     "https://spinzone.darwinbox.in/ms/candidateapi/job?page=1&limit=50"
# ]

for company in COMPANY_NAMES:
    try:
        # Extract company name from URL
        # company_identifier = re.search(r'https://(\w+)\.darwinbox\.in', url).group(1)
        # company_name = COMPANY_NAMES.get(company_identifier, company_identifier)
        
        url=f'https://{COMPANY_NAMES[company]}.darwinbox.in/ms/candidateapi/job?page=1&limit=50'
        company_name = company
        driver.get(url)
        time.sleep(5)  # Wait for Cloudflare
        
        # Wait for the <pre> tag
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "pre")))
        page_source = driver.page_source
        
        # Extract JSON data
        match = re.search(r'<pre>(.*?)</pre>', page_source, re.DOTALL)
        
        if match:
            json_data = match.group(1)
            try:
                data = json.loads(json_data)
                jobs = data.get("message", {}).get("jobs", [])
                
                # Add company name to each job
                for job in jobs:
                    job['company_name'] = company_name
                
                if jobs:
                    all_jobs.extend(jobs)
                    print(f"Found {len(jobs)} jobs from {company_name}")
                else:
                    print(f"No jobs found for {company_name}")
                    
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON for {company_name}: {e}")
        else:
            print(f"JSON not found in the response for {company_name}")
            
    except Exception as e:
        print(f"Error processing {url}: {e}")

driver.quit()

# df = pd.DataFrame(all_jobs)
# df.to_csv('jobs_scrape.csv', index=False)


def authenticate_google_sheets():
    creds = None
    
    # Remove token.json if it exists but is invalid
    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        except ValueError:
            os.remove("token.json")
            print("Removed invalid token.json file")
            creds = None

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                os.remove("token.json")
                creds = None
        
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", 
                    SCOPES,
                    redirect_uri="http://localhost:3000"
                )
                # Force authorization prompt to ensure we get refresh token
                flow.run_local_server(port=3000, access_type='offline', prompt='consent')
                creds = flow.credentials
                
                # Save the credentials for the next run
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
                print("New credentials saved successfully")
            except Exception as e:
                print(f"Error during authentication: {e}")
                raise
    
    return creds

def write_to_google_sheets(jobs):
    try:
        creds = authenticate_google_sheets()
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        # Determine the number of existing rows in the sheet
        result = sheet.values().get(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=SAMPLE_RANGE_NAME
        ).execute()
        
        existing_values = result.get("values", [])
        existing_row_count = len(existing_values)

        # Prepare new data with headers
        values = []
        if jobs:
            keys = jobs[0].keys()
            values.append(list(keys))  # Add headers

            # Add job data
            for job in jobs:
                values.append(list(job.values()))

        # Calculate the number of rows in the new data
        new_row_count = len(values)

        # Clear the existing rows in the sheet
        clear_range = f"Greenhouse!A1:Z"
        sheet.values().clear(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=clear_range
        ).execute()
        print("Cleared existing rows in the Google Sheet.")

        # Write the new data to the sheet
        if values:
            sheet.values().update(
                spreadsheetId=SAMPLE_SPREADSHEET_ID,
                range=SAMPLE_RANGE_NAME,
                valueInputOption="RAW",
                body={"values": values},
            ).execute()
            print(f"Data written to Google Sheets successfully. Total new jobs: {len(jobs)}")
        else:
            print("No jobs to write to Google Sheets.")

    except HttpError as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    write_to_google_sheets(all_jobs)