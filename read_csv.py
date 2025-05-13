import csv
csv_filename = "sensor_log.csv"

print("\nReading the first two rows from the CSV file...")
try:
    with open(csv_filename, mode='r', newline='') as file:
        reader = csv.reader(file)
        # Read header row
        header_row = next(reader, None)
        if header_row:
            print("Header row:", header_row)
        else:
            print("CSV file is empty - no header row found.")
            
        # Read first data row
        data_row = next(reader, None)
        if data_row:
            print("First data row:", data_row)
        else:
            print("No data rows found in the CSV file.")
except Exception as e:
    print(f"Error reading CSV file: {e}")