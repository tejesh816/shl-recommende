import os
import re
import json

# Since the files are in the same directory, we can use the current folder '.'
folder_path = "."
output_file = "catalog.json"

catalog_items = {}

# Regex to match markdown table rows safely
row_regex = re.compile(r"^\s*\|\s*([\d#]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|")

for filename in os.listdir(folder_path):
    if filename.endswith(".md"):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                match = row_regex.match(line)
                if match:
                    num_str = match.group(1).strip()
                    if num_str == "#" or set(num_str) == {"-"}:
                        continue
                    
                    name = match.group(2).strip()
                    test_type = match.group(3).strip()
                    keys = match.group(4).strip()
                    duration = match.group(5).strip()
                    languages = match.group(6).strip()
                    
                    raw_url = match.group(7).strip()
                    clean_url_match = re.search(r"https?://[^\s>)]+", raw_url)
                    url = clean_url_match.group(0) if clean_url_match else raw_url
                    
                    if name not in catalog_items:
                        catalog_items[name] = {
                            "name": name,
                            "url": url,
                            "test_type": test_type,
                            "keys": keys,
                            "duration": duration,
                            "languages": languages
                        }

catalog_list = list(catalog_items.values())

with open(output_file, "w", encoding="utf-8") as out:
    json.dump(catalog_list, out, indent=4, ensure_ascii=False)

print(f"Success! Extracted {len(catalog_list)} unique assessments into '{output_file}'.")