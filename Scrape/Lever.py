from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SAMPLE_SPREADSHEET_ID = "1YmpIPwk8il16xWaT7OlR9iMM0KsrSmjJ-OG29UeNoJU" 
SAMPLE_RANGE_NAME = "Lever!A1"

# Set up Chrome options for headless mode
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Initialize WebDriver
driver = webdriver.Chrome(options=options)

# List of job URLs
# url_list = ["https://jobs.lever.co/paytm", "https://jobs.lever.co/cred"]
COMPANY_NAME=["paytm","cred"]
# Scrape job postings
data = []

for company in COMPANY_NAME:
    # Determine company name from URL
    company_name = company
    url=f"https://jobs.lever.co/{company}"
    # Open the job page
    driver.get(url)

    # Wait for the page to load completely and ensure all jobs are loaded
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "posting"))
    )

    # Add a small delay to ensure all dynamic content is loaded
    time.sleep(3)

    # Find job postings
    jobs = driver.find_elements(By.CLASS_NAME, 'posting')

    for job in jobs:
        try:
            # Extract the job name
            job_name = job.find_element(By.TAG_NAME, 'h5').text.strip()

            # Extract the workplace type with more robust handling
            try:
                workplace_type_elem = job.find_elements(By.CSS_SELECTOR, "div.posting-categories .workplaceTypes")
                workplace_type = workplace_type_elem[0].text.split(" - ")[0].strip() if workplace_type_elem else "N/A"
            except Exception:
                workplace_type = "N/A"
        
            # Extract the location with fallback
            try:
                location_elem = job.find_elements(By.CSS_SELECTOR, "div.posting-categories .sort-by-location")
                location = location_elem[0].text.strip() if location_elem else "N/A"
            except Exception:
                location = "N/A"
            
            # Extract the commitment with fallback
            try:
                commitment_elem = job.find_elements(By.CSS_SELECTOR, "div.posting-categories .commitment")
                commitment = commitment_elem[0].text.strip() if commitment_elem else "N/A"
            except Exception:
                commitment = "N/A"

            # Extract apply link
            try:
                apply_link_elem = job.find_element(By.CLASS_NAME, 'posting-title')
                apply_link = apply_link_elem.get_attribute('href')
            except Exception:
                apply_link = "N/A"
            
            # Only add job if it has a valid job name
            if job_name != "N/A":
                data.append({
                    # 'company_source': company_name,  # New column added 
                    'job name': job_name,
                    'commitment': commitment,
                    'workplace type': workplace_type,
                    'location': location,
                    'apply link': apply_link,
                    'company': company_name,
                })

        except Exception as e:
            print(f"Error processing a job from {company_name}: {e}")

# Save the data to a CSV file
# df = pd.DataFrame(data)
# df.to_csv('jobs_scrape.csv', index=False)

# Close the driver
driver.quit()

# print(f"Scraping complete. Total jobs scraped: {len(data)}. Data saved to jobs_scrape.csv.")



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

        if jobs:
            # Prepare data with headers
            values = [
                list(jobs[0].keys()),  # Headers
                *[list(job.values()) for job in jobs]  # Job data
            ]
            
            # Clear existing sheet and write new data
            # Clear only the rows that previously had data
            # Clear the existing rows in the sheet
            clear_range = f"Greenhouse!A1:Z"
            sheet.values().clear(
                spreadsheetId=SAMPLE_SPREADSHEET_ID,
                range=clear_range
            ).execute()
            print("Cleared existing rows in the Google Sheet.")
            
            sheet.values().update(
                spreadsheetId=SAMPLE_SPREADSHEET_ID,
                range=SAMPLE_RANGE_NAME,
                valueInputOption="RAW",
                body={"values": values},
            ).execute()

            print(f"Sheet updated with {len(jobs)} new jobs.")
        else:
            print("No jobs to write to Google Sheets.")

    except HttpError as err:
        print(f"Error: {err}")


if __name__ == "__main__":
    write_to_google_sheets(data)