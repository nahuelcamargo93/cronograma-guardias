import pandas as pd
import numpy as np

excel_path = "para_importar_enfermeria.xlsx"
xl = pd.ExcelFile(excel_path)

for sheet in xl.sheet_names:
    print(f"\n======================================")
    print(f"SHEET: {sheet}")
    print(f"======================================")
    df = xl.parse(sheet)
    
    # Let's inspect rows and columns to find where dates and names start
    # Let's print shape and the first few columns
    print(f"Original columns length: {len(df.columns)}")
    print(f"Shape: {df.shape}")
    
    # Check if first column has name
    # Let's find first column header
    first_col = df.columns[0]
    print(f"First column name: {first_col}")
    
    # If the first column is unnamed or name isn't clearly the header, let's look at the first few rows
    print("Top 5 rows of first 5 columns:")
    print(df.iloc[:5, :5])
    
    # Let's list all unique values (excluding names and numbers) in the date cells
    # Typically, date columns start after the first column.
    # Let's try to identify date columns: columns that are datetime or strings represent dates, or columns starting from index 1.
    # We will gather all values in columns from index 1 to the end, excluding any final summary columns.
    # Let's find the date columns: they are columns that look like a day of the month or a date.
    # Let's see if there are summary columns at the end (like Total, Horas, etc.)
    # Let's print the last 5 columns
    print("Last 5 columns:")
    print(df.iloc[:5, -5:])
    
    # Collect unique cell values
    cell_values = set()
    for col in df.columns[1:]:
        # check if it is a summary column (usually they have names like "Total", "Horas", "Franco", "F", or "Unnamed: ...")
        # let's see if the column has a date or a number as a day
        # we can just inspect all unique values in these columns
        vals = df[col].dropna().unique()
        for v in vals:
            cell_values.add(v)
            
    print("\nUnique cell values in day columns:")
    print(sorted([str(v) for v in cell_values]))
