from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import json
import csv
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

all_jobs = []

options = Options()
options.headless = True  # Run in headless mode (no browser window)

# Path to your ChromeDriver
driver = webdriver.Chrome(options=options)

# job posting page (API url)

# driver.get("https://delhivery.darwinbox.in/ms/candidateapi/job?page=1&limit=50")
driver.get("https://godigit.darwinbox.in/ms/candidateapi/job?page=1&limit=50")
# driver.get("https://spinzone.darwinbox.in/ms/candidateapi/job?page=1&limit=50")

# Wait for Cloudflare protection to bypass (increase wait time)
time.sleep(20)  # Give Cloudflare time to process the request

# waiting for the <pre> tag to be visible
WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "pre")))

page_source = driver.page_source

match = re.search(r'<pre>(.*?)</pre>', page_source, re.DOTALL)

if match:
    json_data = match.group(1)  # JSON string
    try:
        # checkpoint 1
        print("Raw JSON Data:")  
        data = json.loads(json_data)  
        print("Parsed JSON Data:") 
        
        jobs = data.get("message", {}).get("jobs", [])  # Extract jobs list
        
        if jobs:
            all_jobs.extend(jobs)  
            
            # checkpoint 2
            print(f"Total jobs found: {len(all_jobs)}")  
            
            csv_file = "jobs.csv"

            # CSV headers
            keys = all_jobs[0].keys()

            # checkpoint 3
            # print(f"CSV Headers: {keys}")

            # Writing data to CSV file
            with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=keys)
                writer.writeheader()  
                writer.writerows(all_jobs)  

            print(f"Data exported successfully to {csv_file}. Total jobs: {len(all_jobs)}")
        else:
            print("No jobs found in the response.")
        
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
else:
    print("JSON not found in the response.")
    
driver.quit()
