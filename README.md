# Justin Dearing's christmas card python scriprs

These are script I used in 2024 to cleanse my address book and print out Avery 5160 mailing labels.

## History

In 2010 I got married. This lead to the creation of a google spreadsheet of wedding invitation mailing addresses which became a chirstmas card list. I used the mapquest API to geocode them, and this lasted until 2024 when my API key failed.

So then I geocoded them in python. Then I could not correctly print Avery 5160 labels because Windows kept scaling them. In previous years I borrowed my parents printer. In 2023 it just worked. In 2025 the scaling issue reappeared. After much wailing and gnashing of teeth realized it worked in 2023 because I printed from linux.

## How to use

1. Start up the virtual environment and run `pip install -r requirements.txt`.

2. Make a file called `Christmas Card List - Addresses.csv` and Make it have at least **First Name**, **Last Name** and **Address**

```csv
First Name,Last Name,Address
George, Washington, 1600 Pensylvania Ave
```

3. Create an asure maps account and put the key in `.secrets.toml`

```toml
azure_map_key = "KEY_GOES_HERE"
```

4. Run `python .\geocode_csv.py` to create `Geocoded_Addresses.csv`.

5. Run `create_address_csv.py` to make `For Labels.csv`.

6. Run `print_labels.py` to make `avery_5160_labels.pdf`.

7. Print the PDF. See [here](PrintingFromLinux.md)