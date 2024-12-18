import csv
import json

# Specify the CSV file path
file_path = 'Geocoded_Addresses.csv'
out_path = 'For Labels.csv'

# Initialize an empty list to store the dictionaries
data = []

# Open the file and parse it
with open(file_path, mode='r', newline='', encoding='utf-8') as file:
    # Create a DictReader object
    csv_reader = csv.DictReader(file)
    
    # Convert each row into a dictionary and add it to the list
    for row in csv_reader:
        address = json.loads(row['Azure Address'])
        address['First Name'] = row['First Name']
        address['Last Name'] = row['Last Name']
        data.append(address)

with open(out_path, mode='w', newline='', encoding='utf-8') as out_file:
    columns = set()
    for row in data[:25]:
        columns.update(row.keys())
    csv_writer = csv.DictWriter(out_file, list(columns))
    csv_writer.writeheader()
    csv_writer.writerows(data)
