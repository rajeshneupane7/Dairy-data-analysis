import pandas as pd
import numpy as np
import re

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renames columns dynamically based on an expanded list of keywords.
    Handles potential variations in column naming more gracefully and prevents
    duplicate assignments.
    """
    # Define expanded mappings: {Standard Name: [List of possible keywords]}
    mappings = {
        "date": ["date", "time", "day", "timestamp", "record_date"],
        "cow_id": ["id", "tag", "cow", "animal", "animal_id", "cow_tag"],
        "milk_yield": ["yield", "vol", "liter", "amount", "qty", "production", "milk_amount", "milk_production"],
        "fat_percentage": ["fat", "cream", "fat_content", "fat_%"],
        "protein_percentage": ["prot", "protein", "protein_content", "protein_%"],
        "feed_intake": ["feed", "food", "ration", "intake", "dmi", "dry_matter_intake"],
        "lactation": ["lact", "lactation", "lact_no", "lact_num"],
        "cohort": ["cohort", "group", "pen", "section", "herd_group"]
    }

    new_columns = {}
    used_standards = set() # Tracks which standard names are already assigned

    for col in df.columns:
        col_lower = str(col).lower().strip()
        matched = False
        
        for standard, keywords in mappings.items():
            # Use regex for more robust matching of keywords
            if any(re.search(r'\b' + k + r'\b', col_lower) for k in keywords):
                if standard not in used_standards:
                    new_columns[col] = standard
                    used_standards.add(standard)
                    matched = True
                    break 
        
        if not matched:
            # Clean up the original name if no standard mapping is found
            clean_name = re.sub(r'[^a-zA-Z0-9]+', '_', col_lower).strip('_')
            # Prevent accidental duplicates of standard names
            if clean_name in mappings and clean_name not in used_standards:
                 # If 'date' is cleaned to 'date', but we already have a 'date', avoid collision
                new_columns[col] = f"{clean_name}_original"
            else:
                new_columns[col] = clean_name


    df = df.rename(columns=new_columns)
    
    # --- Type Inference & Cleaning ---
    
    # 1. Handle Date
    if "date" in df.columns:
        # errors='coerce' will turn unparseable dates into NaT (Not a Time)
        df["date"] = pd.to_datetime(df["date"], errors='coerce')
        # Drop rows where the date could not be parsed
        df = df.dropna(subset=["date"])
        # Standardize date format
        df["date"] = df["date"].dt.strftime('%Y-%m-%d')

    # 2. Handle Numeric Columns
    numeric_cols = ["milk_yield", "fat_percentage", "protein_percentage", "feed_intake", "lactation"]
    for col in numeric_cols:
        if col in df.columns:
            # Convert to numeric, coercing errors into NaN, then filling with 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 3. Handle ID (Ensure it's a clean string)
    if "cow_id" in df.columns:
        # Convert to string, remove '.0' for numbers that were floats
        df["cow_id"] = df["cow_id"].astype(str).str.replace(r'\.0$', '', regex=True)

    return df

def generate_smart_alerts(df: pd.DataFrame) -> list[dict]:
    """
    Analyzes the processed dataframe to generate proactive alerts for the producer.
    """
    alerts = []

    if "cow_id" in df.columns and "milk_yield" in df.columns:
        # Calculate average yield per cow
        avg_yields = df.groupby("cow_id")["milk_yield"].mean()

        # Look for the most recent data point for each cow (assuming multiple entries)
        # For simplicity, we compare the current average to a global threshold or 
        # look for significant outliers if we have time series.
        # Here: Identify cows producing 20% less than their own average

        # If we have dates, let's look at the latest date vs previous
        if "date" in df.columns:
            latest_date = df["date"].max()
            recent_data = df[df["date"] == latest_date]

            for _, row in recent_data.iterrows():
                cow = row["cow_id"]
                current_yield = row["milk_yield"]
                cow_avg = avg_yields.get(cow, 0)

                if cow_avg > 0 and current_yield < (cow_avg * 0.8):
                    drop_pct = ((cow_avg - current_yield) / cow_avg) * 100
                    alerts.append({
                        "type": "Health Alert",
                        "cow_id": cow,
                        "message": f"Cow {cow} shows a {drop_pct:.1f}% drop in milk production today.",
                        "severity": "High"
                    })

    if "fat_percentage" in df.columns:
        low_fat_cows = df[df["fat_percentage"] < 3.0]["cow_id"].unique()
        if len(low_fat_cows) > 0:
            alerts.append({
                "type": "Nutritional Alert",
                "message": f"{len(low_fat_cows)} cows have fat percentage below 3.0%, suggesting potential SARA or diet issues.",
                "severity": "Medium"
            })

    return alerts