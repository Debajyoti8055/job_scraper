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
SAMPLE_RANGE_NAME = "Dezerv!A1"

# Company name mapping
COMPANY_NAMES = {
    "Dezerv": "dezerv",
}

all_jobs = []
all_fields = set()

# Flatten JSON utility
def flatten_json(nested_json, parent_key="", sep="_"):
    items = []
    for k, v in nested_json.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, json.dumps(v)))
        else:
            items.append((new_key, v))
    return dict(items)

# Set up headless Chrome WebDriver
options = Options()
options.headless = True
driver = webdriver.Chrome(options=options)

for company in COMPANY_NAMES:
    try:
        url = f'https://api.{COMPANY_NAMES[company]}.in/v1/job-postings?limit=500&sourceId=1'
        driver.get(url)
        time.sleep(5)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "pre")))
        page_source = driver.page_source
        match = re.search(r'<pre>(.*?)</pre>', page_source, re.DOTALL)
        
        if match:
            json_data = match.group(1)
            try:
                data = json.loads(json_data)
                jobs = data.get("data", [])
                
                for job in jobs:
                    job['company_name'] = company
                    job.pop("content", None)  # Remove content field
                    all_fields.update(job.keys())
                    all_jobs.append(job)
                
                print(f"Found {len(jobs)} jobs from {company}")
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON for {company}: {e}")
        else:
            print(f"JSON not found in the response for {company}")
            
    except Exception as e:
        print(f"Error processing {url}: {e}")

driver.quit()

# Flatten all job data
flattened_jobs = [flatten_json(job) for job in all_jobs]
df = pd.DataFrame(flattened_jobs)
df.to_csv('jobs_scrape.csv', index=False)

def authenticate_google_sheets():
    creds = None
    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        except ValueError:
            os.remove("token.json")
            creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                os.remove("token.json")
                creds = None
        
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                flow.run_local_server(port=3000, access_type='offline', prompt='consent')
                creds = flow.credentials
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
            except Exception as e:
                raise
    
    return creds

def get_funding_stages():
    try:
        creds = authenticate_google_sheets()
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        # Read "Company DB" sheet
        result = sheet.values().get(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range="Company DB!A:B"  # Assuming Column A: Company Name, Column B: Funding Stage
        ).execute()

        values = result.get("values", [])

        # Create dictionary {company_name: funding_stage}
        funding_dict = {row[0]: row[1] for row in values[1:] if len(row) > 1}  # Skip header row
        return funding_dict

    except HttpError as err:
        print(f"Error fetching funding stages: {err}")
        return {}
    
def write_to_google_sheets(jobs):
    try:
        creds = authenticate_google_sheets()
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME).execute()
        existing_values = result.get("values", [])
        existing_row_count = len(existing_values)

        funding_dict = get_funding_stages()
        
        EXCLUDED_FIELDS={"coordinatorName","hiringManagerId","hiringManagerName","jobLevel","orgUnitId",""}

        values = []
        if jobs:
            filtered_jobs = [
                {k: v for k, v in job.items() if k not in EXCLUDED_FIELDS}
                for job in jobs
            ]
            # keys = sorted(set().union(*[job.keys() for job in jobs]))  # Collect all unique keys
            # values.append(keys)  # Header row
            keys = list(filtered_jobs[0].keys())+["Funding Stage"]
            values = [keys]

            # for job in jobs:
            #     row = [job.get(key, "") for key in keys]  # Ensure all rows follow the header structure
            #     values.append(row)

            for job in filtered_jobs:
                company_name = job["company_name"]
                funding_stage = funding_dict.get(company_name, "Unknown")  # Default to "Unknown"
                values.append([job.get(k, "") for k in filtered_jobs[0].keys()] + [funding_stage])



        if existing_row_count > 0:
            clear_range = f"Dezerv!A1:Z"
            sheet.values().clear(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=clear_range).execute()

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
    write_to_google_sheets(flattened_jobs)
