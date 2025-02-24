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
SAMPLE_RANGE_NAME = "SenseHQ!A1"

# Set up Chrome options for headless mode
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Initialize WebDriver
driver = webdriver.Chrome(options=options)

# List of job URLs
company_list = ["groww"]


# Scrape job postings
data = []

for company in company_list:
    # Determine company name from URL
    url = f'https://{company}.sensehq.com/careers/jobs?page=0&pageSize=50'
    company_name = company
    
    # Open the job page
    driver.get(url)

    # Wait for the page to load completely and ensure all jobs are loaded
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "css-1tk7xz5"))
    )

    # Add a small delay to ensure all dynamic content is loaded
    time.sleep(3)

    # Find job postings
    jobs = driver.find_elements(By.CLASS_NAME, 'css-1tk7xz5')

    for job in jobs:
        try:
            # Extract the job name
            job_name = job.find_element(By.CSS_SELECTOR, 'div.css-beqgbl .css-8qk9uv').text.strip()

            # Extract department
            try:
                department = job.find_element(By.CLASS_NAME, 'css-1cm4lgc').text.strip()
            except Exception:
                department = "N/A"
            
            # Extract experience
            try:
                experience = job.find_element(By.CLASS_NAME, 'css-dbazfu').text.strip()
            except Exception:
                experience = "N/A"
            
            # Extract Apply link
            # try:
            #     apply_link = job.find_element(By.CLASS_NAME, 'css-1l8s4l0').get_attribute('href')
            # except Exception:
            #     apply_link = "N/A"
            
            # Only add job if it has a valid job name
            if job_name != "N/A":
                data.append({
                    # 'company_source': company_name,  # New column added 
                    'job name': job_name,
                    'department': department,
                    'experience': experience,
                    # 'apply link': apply_link,
                    'company': company_name,
                })

        except Exception as e:
            print(f"Error processing a job from {company_name}: {e}")

# Save the data to a CSV file
df = pd.DataFrame(data)
df.to_csv('jobs_scrape.csv', index=False)

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
            sheet.values().clear(
                spreadsheetId=SAMPLE_SPREADSHEET_ID,
                range=SAMPLE_RANGE_NAME
            ).execute()
            
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