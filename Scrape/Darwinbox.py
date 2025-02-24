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
    "Delhivery": "delhivery",
    "Digit Insurance": "godigit",
    "Spinny": "spinzone",
    "Rapido":"rapido",
    "HealthifyMe":"healthify"
}

all_jobs = []

options = Options()
options.headless = True

driver = webdriver.Chrome(options=options)

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
                    job['Company Name'] = company_name
                    job["Apply Link"]=f"https://{COMPANY_NAMES[company]}.darwinbox.in/ms/candidate/careers/{job['id']}"
                
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

def get_company_data():
    try:
        creds = authenticate_google_sheets()
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range="Company DB!A:C"  # Column A: Company Name, B: Funding Stage, C: Industry
        ).execute()
        values = result.get("values", [])
        return {row[0]: (row[1], row[2]) for row in values[1:] if len(row) > 2}  # Skip header
    except HttpError as err:
        print(f"Error fetching company data: {err}")
        return {}

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
        
        # Fetch funding stages
        funding_dict = get_company_data()
        
        EXCLUDED_FIELDS = {"designation_display_name","officelocation_arr","department_id","emp_type_id","functional_area","tool_tip_locations","functional_area_id","timezone"}


        # Prepare new data with headers
        values = []
        if jobs:
            filtered_jobs = [
                {k: v for k, v in job.items() if k not in EXCLUDED_FIELDS}
                for job in jobs
            ]
            # keys = jobs[0].keys()
            # values.append(list(keys))  # Add headers

            # Define column name mappings
            COLUMN_RENAME_MAP = {
                "title": "Job Title",
                "officelocation_show_arr": "Job Location",
                "id": "Job Id",
                "experience_from_num":"Experience From",
                "experience_to_num":"Experience To",
                "emp_type":"Employment Type",
            }

            # Rename keys in headers
            keys = [COLUMN_RENAME_MAP.get(k, k) for k in filtered_jobs[0].keys()] + ["Funding Stage", "Industry"]

            values = [keys]

            # Add job data
            # for job in jobs:
            #     values.append(list(job.values()))
            for job in filtered_jobs:
                company_name = job["Company Name"]
                funding_stage,industry = funding_dict.get(company_name, ("Unknown", "Unknown"))  # Default to "Unknown"
                values.append([job.get(k, "") for k in filtered_jobs[0].keys()] + [funding_stage,industry])

        # Calculate the number of rows in the new data
        new_row_count = len(values)

        # Clear the existing rows in the sheet
        clear_range = f"Darwinbox!A1:Z"
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