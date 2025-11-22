# data.py

#Library
import pandas as pd
import os

def clean_data(file_path="travel_data.xlsx", output_path="cleaned_output.xlsx"):
    #Check if file exists
    if not os.path.exists(file_path):
        #1- Not exists: It will stops and shows an error
        raise FileNotFoundError(f"The file: '{file_path}' not found")
    #2- Exists:
    #load file
    df = pd.read_excel(file_path)
    
    # List of unnecessary columns 
    cols_to_drop = [
        "nightlife",
        "latitude",
        "longitude",
        "id",
        "ideal_durations",
        "avg_temp_monthly"
    ]
    #Drop columns and save cleaned data
    df = df.drop(columns=cols_to_drop, errors="ignore")
    df.to_excel(output_path, index=False)
    print(f"✅ Cleaned data saved as '{output_path}'")
    return df


def load_cleaned_data(file_path="cleaned_output.xlsx"):
    
    #Check if cleaned data exists 
    if not os.path.exists(file_path): 
        #1- Not exists: it  will calls clean_data() to create it
        print("Cleaned file not found. Creating it now")
        clean_data(output_path=file_path)
    #2- Exists: it will load cleaned data
    df = pd.read_excel(file_path)
    return df

