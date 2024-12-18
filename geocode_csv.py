import json
import pandas as pd
import requests
from urllib.parse import quote

from config import settings

# Input and output file paths
input_csv = './Christmas Card List - Addresses.csv'
output_csv = './Geocoded_Addresses.csv'

headers = {
    'User-Agent': 'Justin Dearing Cristmas Card GeoCoder/1.0 (zippy1981@gmail.com)'
}

# Read the input CSV file
data = pd.read_csv(input_csv,)

# Filter out rows where the Address column is empty or whitespace
data = data.dropna(subset=['Address']).reset_index(drop=True)

# Function to geocode an address using OpenStreetMap's Nominatim API
def geocode_address_osm(address):
    try:
        # Construct the OSM URL
        url = f"https://nominatim.openstreetmap.org/search?q={quote(address)}&format=json&addressdetails=1&limit=1"

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()

        if result:
            return {
                'VerifiedAddress': result[0].get('address', {}),
                'DisplayAddress': result[0].get('display_name', '')
            }
        else:
            return {'VerifiedAddress': {}, 'DisplayAddress': ''}
    except Exception as e:
        print(f"Error geocoding address '{address}': {e}")
        return {'VerifiedAddress': {}, 'DisplayAddress': ''}

def geocode_address_azure(address):
    try:
        # Construct the OSM URL
        url = f"https://atlas.microsoft.com/search/address/json?api-version=1.0&query={quote(address)}&subscription-key={settings.azure_map_key}"

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()['results'][0]

        if result:
            return {
                'VerifiedAddress': result.get('address', {}),
                'Confidence': result.get('score', 0)
            }
        else:
            return {'VerifiedAddress': {}, 'Confidence': 0}
    except Exception as e:
        print(f"Error geocoding address '{address}': {e}")
        return {'VerifiedAddress': {}, 'Confidence': 0}

# Apply the geocoding function to each row
data['OSM_URL'] = data['Address'].apply(lambda addr: f"https://nominatim.openstreetmap.org/search?q={quote(addr)}&format=json&addressdetails=1&limit=1")
data['BINGMAPS_URL'] = data['Address'].apply(lambda addr: f"https://atlas.microsoft.com/search/address/json?api-version=1.0&query={quote(addr)}&subscription-key=___KEY_HERE___")
osm_results = data['Address'].apply(geocode_address_osm)

# Extract the geocoded results into separate columns
data['OSM Address'] = osm_results.apply(lambda x: json.dumps(x['VerifiedAddress']))
data['OSM DisplayAddress'] = osm_results.apply(lambda x: x['DisplayAddress'])

osm_columns = set()

# Not all the JSON  has all the keys so we go in 25 rows
for row in osm_results[:25]:
    osm_columns.update(row['VerifiedAddress'].keys())

bing_results = data['Address'].apply(geocode_address_azure)

data['Azure Address'] = bing_results.apply(lambda x: json.dumps(x['VerifiedAddress']))
data['Azure Score'] = bing_results.apply(lambda x: x['Confidence'])

#for col in geocoded_columns:
#    data[col] = data['VerifiedAddress'].apply(lambda x: x.get(col, ''))

#data["Address 1"] = data.apply(lambda x: '{house_number} {road}'.format(**x.to_dict()), 1)
#data["Address City"] = data.apply(lambda x: x['town'] or x['village'] or x['hamlet'] or x['city'] or x['suburb'], axis=1)

# Select and rename the relevant columns for the output
# output_data = data[["First Name", "Last Name", 'Address 1', 'Address City', "Address", "DisplayAddress", "VerifiedAddress"] + list(geocoded_columns)]
output_data = data

# Export the results to a new CSV file
output_data.to_csv(output_csv, index=False)

print(f"Geocoded addresses saved to {output_csv}")
