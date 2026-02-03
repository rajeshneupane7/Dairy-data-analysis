import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Configuration
API_UPLOAD_URL = "http://backend:8000/upload"  # 'backend' is the docker service name
API_INSIGHTS_URL = "http://backend:8000/generate_insights"

st.set_page_config(page_title="DairyPro Analytics", layout="wide")

st.title("🐄 DairyPro Analytics Dashboard")
st.markdown("Upload your raw Excel or CSV files to generate instant insights.")

# --- Sidebar: File Upload ---
st.sidebar.header("Data Import")
uploaded_file = st.sidebar.file_uploader("Upload Herd Data", type=["csv", "xlsx"])

if uploaded_file is not None:
    with st.spinner('Sending data to AI standardization engine...'):
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            response = requests.post(API_UPLOAD_URL, files=files)
            
            if response.status_code == 200:
                result = response.json()
                df = pd.DataFrame(result["data"])
                
                st.sidebar.success(f"Processed {result['rows']} records!")

                # --- Debugging: Display DataFrame info ---
                st.write("--- Debug Info (DataFrame) ---")
                st.write(f"DataFrame columns: {df.columns.tolist()}")
                st.write("DataFrame head:")
                st.dataframe(df.head())
                st.write("--- End Debug Info (DataFrame) ---")
                
                # --- KPI Section ---
                st.subheader("Key Performance Indicators (KPIs)")
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                
                if "milk_yield" in df.columns:
                    total_yield = df["milk_yield"].sum()
                    avg_yield = df["milk_yield"].mean()
                    kpi1.metric("Total Production", f"{total_yield:,.0f} L")
                    kpi2.metric("Avg Yield / Cow", f"{avg_yield:.2f} L")
                
                if "cow_id" in df.columns:
                    kpi3.metric("Active Herd Size", f"{df['cow_id'].nunique()}")

                if "fat_percentage" in df.columns:
                     kpi4.metric("Avg Fat Content", f"{df['fat_percentage'].mean():.2f}%")

                st.divider()

                # --- Visualizations ---
                st.subheader("Standard Visualizations")
                col1, col2 = st.columns(2)

                # Chart 1: Production Over Time
                if "date" in df.columns and "milk_yield" in df.columns:
                    daily_yield = df.groupby("date")["milk_yield"].sum().reset_index()
                    fig_line = px.line(daily_yield, x="date", y="milk_yield", 
                                       title="Milk Production Trend", markers=True)
                    col1.plotly_chart(fig_line, use_container_width=True)
                else:
                    col1.info("Cannot display Milk Production Trend: Missing 'date' or 'milk_yield' columns.")

                # Chart 2: Yield Distribution (Box Plot or Histogram)
                if "milk_yield" in df.columns:
                    fig_hist = px.histogram(df, x="milk_yield", nbins=20, 
                                            title="Yield Distribution (Herd Health)")
                    col2.plotly_chart(fig_hist, use_container_width=True)
                else:
                    col2.info("Cannot display Yield Distribution: Missing 'milk_yield' column.")

                # Chart 3: Performance by Cow (Top 10)
                if "cow_id" in df.columns and "milk_yield" in df.columns:
                    top_cows = df.groupby("cow_id")["milk_yield"].sum().nlargest(10).reset_index()
                    top_cows["cow_id"] = top_cows["cow_id"].astype(str)
                    
                    fig_bar = px.bar(top_cows, x="cow_id", y="milk_yield", 
                                     title="Top 10 Producing Cows", color="milk_yield")
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("Cannot display Top 10 Producing Cows: Missing 'cow_id' or 'milk_yield' columns.")

                st.divider()

                        # --- AI-Generated Insights ---
                st.subheader("AI-Generated Insights")
                with st.spinner('Generating AI insights with Llama3...'):
                        try:
                            insights_response = requests.post(API_INSIGHTS_URL, json={"columns": list(df.columns)})
                            
                            # --- Debugging: Display raw AI response ---
                            st.write("--- Debug Info (AI Insights Raw Response) ---")
                            st.write(f"AI Insights Status Code: {insights_response.status_code}")
                            st.write(f"AI Insights Raw Text: {insights_response.text}")
                            st.write("--- End Debug Info (AI Insights Raw Response) ---")
    
                            if insights_response.status_code == 200:
                                ai_insights = insights_response.json()
                                # --- Debugging: Display parsed AI insights ---
                                st.write("--- Debug Info (Parsed AI Insights) ---")
                                st.write("Parsed AI Insights:")
                                st.write(ai_insights)
                                st.write("--- End Debug Info (Parsed AI Insights) ---")
                        except requests.RequestException as e:
                            st.error(f"Error generating AI insights: {str(e)}")
        except requests.RequestException as e:
                st.error(f"Error uploading file: {str(e)}")
