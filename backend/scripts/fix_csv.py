
import csv
import shutil

INPUT_FILE = "backend/app/data/enriched_master_chart.csv"
OUTPUT_FILE = "backend/app/data/enriched_master_chart_fixed.csv"

def fix():
    # Read all rows
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Detect duplicates
    code_map = {} # code -> list of rows
    all_codes = set()
    
    for row in rows:
        c = row['code']
        if c not in code_map:
            code_map[c] = []
        code_map[c].append(row)
        all_codes.add(c)

    fixed_rows = []
    
    # Process
    # We want to keep original order? Or simply rebuild.
    # Rebuilding from code_map loses order but order might not matter?
    # Better to iterate `rows` but handle resolved duplicates.
    
    # First pass: resolve duplicates
    renames = {} # old_row_id -> new_code
    
    for code, row_list in code_map.items():
        if len(row_list) == 1:
            continue
            
        print(f"Processing duplicate code: {code} ({len(row_list)} entries)")
        
        # Find Header
        header_row = None
        detail_rows = []
        for r in row_list:
            if r['type'] == 'Header':
                header_row = r
            else:
                detail_rows.append(r)
                
        if header_row and detail_rows:
            # Keep header as is
            # Renumber details
            
            # Find a free code near this one
            base_code_int = int(code)
            for i, detail in enumerate(detail_rows):
                # Try finding free code
                offset = 1
                while True:
                    candidate = str(base_code_int + offset)
                    if candidate not in all_codes:
                        # Found one!
                        print(f"  Renaming duplicate '{detail['description']}' from {code} to {candidate}")
                        detail['code'] = candidate
                        all_codes.add(candidate)
                        break
                    offset += 1
        elif len(detail_rows) > 1 and not header_row:
             # Multiple details? Just renumber all but first?
             print("  Multiple details no header. Renumbering duplicates.")
             # Keep first
             for i in range(1, len(detail_rows)):
                 detail = detail_rows[i]
                 offset = 1
                 base_code_int = int(code)
                 while True:
                    candidate = str(base_code_int + offset)
                    if candidate not in all_codes:
                        print(f"  Renaming duplicate '{detail['description']}' from {code} to {candidate}")
                        detail['code'] = candidate
                        all_codes.add(candidate)
                        break
                    offset += 1

    # Now write back
    with open(INPUT_FILE, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    print("CSV fixed.")

if __name__ == "__main__":
    fix()
