'''
to-do

1. remove {id, designation_display_name, officelocation_arr, department_id, emp_type_id,functional_area, functional_area_id, experience_from_num, experience_to_num}
2. add experience(from-to)
3. format created_on
'''

import csv

input_csv = 'jobs.csv'
output_csv = 'cleaned_data.csv'

# Columns to remove
columns_to_remove = ['id', 'designation_display_name', 'officelocation_arr', 'department_id', 'emp_type_id', 'functional_area', 'functional_area_id', 'experience_from_num', 'experience_to_num']

with open(input_csv, mode='r', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    
    # Get the fieldnames (headers) and filter out the columns to remove
    fieldnames = [field for field in reader.fieldnames if field not in columns_to_remove]
    
    # Add the new 'experience' column to the fieldnames
    fieldnames.append('experience(from-to)')

    with open(output_csv, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        writer.writeheader()
        
        for row in reader:
            # Combine experience_from_num and experience_to_num into 'experience(from-to)'
            experience_from = row.get('experience_from_num', '')
            experience_to = row.get('experience_to_num', '')
            experience_combined = f"{experience_from}-{experience_to}" if experience_from and experience_to else (experience_from or experience_to)
            
            # Remove the unwanted columns and add the combined experience column
            cleaned_row = {key: value for key, value in row.items() if key not in columns_to_remove}
            cleaned_row['experience(from-to)'] = experience_combined
            
            # Clean the 'created_on' field to only contain the date part before 'T'
            created_on = row.get('created_on', '')
            if 'T' in created_on:
                created_on = created_on.split('T')[0]  # Extract the date part
            cleaned_row['created_on'] = created_on
            
            # Write the cleaned row
            writer.writerow(cleaned_row)

print(f"CSV file cleaned successfully with combined experience and formatted created_on date. The cleaned file is saved as '{output_csv}'.")
