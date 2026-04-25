from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import pandas as pd
import io
import numpy as np
import requests
import json

from data_processor import standardize_columns, generate_smart_alerts 

# --- Pydantic Model for Insights Request ---
class InsightRequest(BaseModel):
    columns: list[str]

app = FastAPI(title="Dairy Analytics API")

OLLAMA_URL = "http://host.docker.internal:11434/api/generate"

@app.get("/")
def health_check():
    return {"status": "active", "service": "dairy-backend"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Invalid file format.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {e}")

    try:
        processed_df = standardize_columns(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Standardization Error: {e}")

    # Replace infinities and NaNs with finite values before JSON serialization
    processed_df = processed_df.replace([np.inf, -np.inf], np.nan)

    # Round all float columns to prevent "out of range" JSON errors
    for col in processed_df.select_dtypes(include=[np.number]).columns:
        processed_df[col] = processed_df[col].round(4)

    # After rounding, fill any remaining NaNs with 0 so JSON encoding never sees NaN/inf
    processed_df = processed_df.fillna(0)

    alerts = generate_smart_alerts(processed_df)

    return {
        "filename": file.filename,
        "rows": len(processed_df),
        "columns": list(processed_df.columns),
        "data": processed_df.to_dict(orient="records"),
        "alerts": alerts
    }

@app.post("/generate_insights")
async def generate_insights(req: InsightRequest):
    prompt = f"""
    You are an expert agricultural data analyst specializing in the dairy industry.
    Given the following available data columns, please suggest three insightful visualizations.
    For each visualization, provide a title, a chart type (from 'bar', 'line', 'scatter', 'histogram', 'box'), the columns to use for the x and y axes, and a brief justification explaining what insight the chart would provide.

    Available columns: {', '.join(req.columns)}

    Return the response as a valid JSON array, where each object has the keys "title", "chart_type", "x", "y", and "justification". Do not include any other text or explanations outside of the JSON array.
    
    Example format:
    [
        {{
            "title": "Milk Yield vs. Feed Intake",
            "chart_type": "scatter",
            "x": "feed_intake",
            "y": "milk_yield",
            "justification": "This helps determine the relationship between how much a cow eats and how much milk it produces, identifying efficient feeders."
        }}
    ]
    """

    try:
        payload = {
            "model": "llama3.2",
            "prompt": prompt,
            "format": "json",
            "stream": False
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()

        ollama_response_json = response.json()
        print(f"Raw Ollama response: {ollama_response_json}") # Debug print
        # The response from Ollama is a JSON string in the 'response' field
        # We need to parse this inner JSON
        insights_data = json.loads(ollama_response_json["response"])
        
        # Normalize the response to always be a list
        if isinstance(insights_data, dict):
            # Look for common wrapper keys
            for key in ["result", "visualizations", "insights", "data"]:
                if key in insights_data and isinstance(insights_data[key], list):
                    return insights_data[key]
            # If it's a dict but no known list key is found, return as a single-item list or empty
            return [insights_data] if insights_data else []
        
        return insights_data

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Could not connect to the AI model: {e}")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing Ollama response: {e}") # More specific error logging
        raise HTTPException(status_code=500, detail=f"Failed to parse AI model response: {e}")