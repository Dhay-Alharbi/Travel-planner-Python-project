# data.py
import pandas as pd
import os

def clean_data(file_path="travel_data.xlsx", output_path="cleaned_output.xlsx"):
    """
    Clean the raw travel data and save it as a new Excel file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Raw data file '{file_path}' not found!")

    df = pd.read_excel(file_path)
    
    # Drop unnecessary columns
    cols_to_drop = [
        "nightlife",
        "latitude",
        "longitude",
        "id",
        "ideal_durations",
        "avg_temp_monthly"
    ]
    
    df = df.drop(columns=cols_to_drop, errors="ignore")
    df.to_excel(output_path, index=False)
    print(f"✅ Cleaned data saved as '{output_path}'")
    return df


def load_cleaned_data(file_path="cleaned_output.xlsx"):
    """
    Load cleaned data. If not found, clean the raw data first.
    """
    if not os.path.exists(file_path):
        print("⚠️ Cleaned data file not found. Cleaning raw data first...")
        clean_data(output_path=file_path)
    df = pd.read_excel(file_path)
    return df
