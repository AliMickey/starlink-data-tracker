import json
import os
import sys

MAX_SIZE_BYTES = 500000
ALLOWED_ADDITIONS = (1, 2)
BASE_FILE_PATH = "base_mapping.json"
HEAD_FILE_PATH = "app/static/other/city-mapping.json"

try:
    # Check file size
    file_size = os.path.getsize(HEAD_FILE_PATH)
    if file_size > MAX_SIZE_BYTES:
        print(f"Error: File size ({file_size} bytes) exceeds the limit of {MAX_SIZE_BYTES} bytes.")
        sys.exit(1)

    # Check for valid JSON format
    with open(HEAD_FILE_PATH, 'r') as f:
        new_data = json.load(f)

except json.JSONDecodeError:
    print("Error: Invalid JSON format.")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)

try:
    with open(BASE_FILE_PATH, 'r') as f:
        old_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    print("Error: Invalid JSON format.")
    sys.exit(1)

old_keys = set(old_data.keys())
new_keys = set(new_data.keys())

# Rule a: No keys can be deleted.
if not old_keys.issubset(new_keys):
    print("Validation failed: Deletions or key renames are not allowed.")
    sys.exit(1)

# Rule b: Values of existing keys cannot be modified.
for key in old_keys:
    if old_data[key] != new_data[key]:
        print(f"Validation failed: Modification of value for key '{key}' is not allowed.")
        sys.exit(1)

# Rule c: Must add an allowed number of new keys.
added_keys_count = len(new_keys - old_keys)
if added_keys_count not in ALLOWED_ADDITIONS:
    print(f"Validation failed: Found {added_keys_count} new entries. Only {ALLOWED_ADDITIONS} are allowed.")
    sys.exit(1)

sys.exit(0)
