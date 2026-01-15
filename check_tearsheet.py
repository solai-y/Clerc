import csv
import sys

# Increase the field size limit for large CSV fields
csv.field_size_limit(sys.maxsize)

def check_tearsheet_in_csv(csv_path):
    """Check for 'tearsheet' in secondary or tertiary columns of the CSV."""

    tearsheet_rows = []
    total_rows = 0

    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)

            # Check if required columns exist
            if 'secondary' not in csv_reader.fieldnames and 'tertiary' not in csv_reader.fieldnames:
                print("Error: CSV does not contain 'secondary' or 'tertiary' columns")
                print(f"Available columns: {csv_reader.fieldnames}")
                return

            print(f"Columns found: {csv_reader.fieldnames}")
            print("\nSearching for 'tearsheet' in secondary and tertiary columns...\n")

            for row_num, row in enumerate(csv_reader, start=2):  # start=2 because row 1 is header
                total_rows += 1

                secondary = row.get('secondary', '').lower()
                tertiary = row.get('tertiary', '').lower()

                if 'tearsheet' in secondary or 'tearsheet' in tertiary:
                    tearsheet_rows.append({
                        'row_num': row_num,
                        'secondary': row.get('secondary', ''),
                        'tertiary': row.get('tertiary', ''),
                        'primary': row.get('primary', ''),  # Include primary for context
                    })

        # Display results
        print(f"Total rows processed: {total_rows}")
        print(f"Rows containing 'tearsheet': {len(tearsheet_rows)}\n")

        if tearsheet_rows:
            print("=" * 80)
            print("ROWS WITH 'TEARSHEET':")
            print("=" * 80)
            for item in tearsheet_rows:
                print(f"\nRow {item['row_num']}:")
                print(f"  Primary:   {item['primary']}")
                print(f"  Secondary: {item['secondary']}")
                print(f"  Tertiary:  {item['tertiary']}")
                print("-" * 80)
        else:
            print("No rows found with 'tearsheet' in secondary or tertiary columns.")

    except FileNotFoundError:
        print(f"Error: File not found at {csv_path}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    csv_path = "backend/ai-service/training_data_text.csv"
    check_tearsheet_in_csv(csv_path)
