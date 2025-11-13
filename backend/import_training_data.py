"""
Import existing training_data_text.csv into retraining_data table
"""
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

supabase = create_client(supabase_url, supabase_key)

def get_all_tags() -> Dict[str, int]:
    """Fetch all tags from database and create name -> id mapping"""
    print("Fetching tags from database...")
    response = supabase.table('tags').select('id, tag_name').execute()

    tag_map = {}
    for tag in response.data:
        tag_map[tag['tag_name']] = tag['id']

    print(f"✓ Loaded {len(tag_map)} tags")
    return tag_map

def normalize_tag_name(tag_name: str) -> str:
    """Normalize tag name for matching (handle spaces, underscores, etc)"""
    return tag_name.strip().replace('_', ' ').replace('-', ' ').lower()

def find_tag_id(tag_name: str, tag_map: Dict[str, int]) -> int | None:
    """Find tag ID with fuzzy matching"""
    if not tag_name or pd.isna(tag_name) or tag_name.strip() == '':
        return None

    # Try exact match first
    if tag_name in tag_map:
        return tag_map[tag_name]

    # Try normalized match
    normalized = normalize_tag_name(tag_name)
    for db_tag_name, tag_id in tag_map.items():
        if normalize_tag_name(db_tag_name) == normalized:
            return tag_id

    return None

def import_training_data(csv_path: str):
    """Import training data from CSV into retraining_data table"""
    print(f"\nReading CSV from: {csv_path}")
    df = pd.read_csv(csv_path)

    print(f"✓ Loaded {len(df)} rows from CSV")
    print(f"Columns: {list(df.columns)}")

    # Validate columns
    required_cols = {'primary', 'secondary', 'tertiary', 'text'}
    if not required_cols.issubset(set(df.columns)):
        raise ValueError(f"CSV must have columns: {required_cols}")

    # Get all tags from database
    tag_map = get_all_tags()

    # Process each row
    print("\nProcessing rows...")
    imported = 0
    skipped = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            # Extract tag names
            primary_name = row['primary']
            secondary_name = row['secondary']
            tertiary_name = row['tertiary']
            text = row['text']

            # Skip if no text
            if not text or pd.isna(text) or str(text).strip() == '':
                skipped += 1
                continue

            # Look up tag IDs
            primary_ids = []
            secondary_ids = []
            tertiary_ids = []

            if primary_name and not pd.isna(primary_name):
                primary_id = find_tag_id(str(primary_name), tag_map)
                if primary_id:
                    primary_ids.append(primary_id)

            if secondary_name and not pd.isna(secondary_name):
                secondary_id = find_tag_id(str(secondary_name), tag_map)
                if secondary_id:
                    secondary_ids.append(secondary_id)

            if tertiary_name and not pd.isna(tertiary_name):
                tertiary_id = find_tag_id(str(tertiary_name), tag_map)
                if tertiary_id:
                    tertiary_ids.append(tertiary_id)

            # Insert into database
            insert_data = {
                'document_id': None,  # NULL for synthetic training data
                'document_text': str(text),
                'primary_tag_ids': primary_ids if primary_ids else None,
                'secondary_tag_ids': secondary_ids if secondary_ids else None,
                'tertiary_tag_ids': tertiary_ids if tertiary_ids else None
            }

            supabase.table('retraining_data').insert(insert_data).execute()
            imported += 1

            if (imported + skipped) % 100 == 0:
                print(f"  Processed {imported + skipped} rows... (imported: {imported}, skipped: {skipped})")

        except Exception as e:
            errors.append(f"Row {idx}: {str(e)}")
            skipped += 1

    print(f"\n{'='*60}")
    print(f"Import complete!")
    print(f"  ✓ Imported: {imported} rows")
    print(f"  ⊗ Skipped: {skipped} rows")

    if errors:
        print(f"\n⚠ Errors encountered:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")

if __name__ == "__main__":
    import sys

    csv_path = sys.argv[1] if len(sys.argv) > 1 else "./ai-service/training_data_text.csv"

    print("="*60)
    print("Training Data Import Tool")
    print("="*60)

    # Confirm before proceeding
    response = input(f"\nImport training data from: {csv_path}\nContinue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Import cancelled.")
        sys.exit(0)

    import_training_data(csv_path)
