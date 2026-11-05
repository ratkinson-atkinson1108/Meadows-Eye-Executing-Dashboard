from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import json

app = FastAPI()

# Allow your Google Apps Script to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process-dashboard")
async def process_dashboard(
    charge_file: UploadFile = File(...),
    payment_file: UploadFile = File(...),
    master_file: UploadFile = File(...)
):
    try:
        # 1. Read files into Pandas DataFrames in milliseconds
        df_charge = pd.read_excel(io.BytesIO(await charge_file.read()))
        df_payment = pd.read_excel(io.BytesIO(await payment_file.read()))
        df_master = pd.read_excel(io.BytesIO(await master_file.read()))
        
        # --- DATA PROCESSING (PANDAS) ---
        # Example: Fill missing values and ensure dates are proper datetime objects
        df_charge['DOS'] = pd.to_datetime(df_charge.iloc[:, 11], errors='coerce') # Column L
        df_charge['First Billed Date'] = pd.to_datetime(df_charge.iloc[:, 13], errors='coerce') # Column N
        
        # Initialize the dictionaries exactly as your JS expects
        globalKpiData = {}
        globalRawAgingPaid = []
        globalRawClientView = []
        
        # Example: Grouping KPI Data instantly using Pandas (replaces your 100-line JS loop)
        # We group by the Year and Month of the First Billed Date
        df_charge['Year'] = df_charge['First Billed Date'].dt.year
        df_charge['Month'] = df_charge['First Billed Date'].dt.month
        
        # Aggregate totals instantly
        kpi_summary = df_charge.groupby(['Year', 'Month']).agg(
            Count=('Claim ID', 'count'),
            Total_Billed=('Billed Amount', 'sum'),
            Ins_Balance=('Insurance Balance', 'sum'),
            Pat_Balance=('Patient Balance', 'sum')
        ).reset_index()

        # (You will move the rest of your math logic into Pandas here. 
        # Pandas handles filtering and merging in 1 line of code instead of nested JS loops).

        # 2. Package the payload to match your frontend variables
        payload = {
            "globalKpiData": globalKpiData, # Replace with your mapped dict
            "globalKpiDataDOS": {}, 
            "globalRawAgingPaid": globalRawAgingPaid,
            "globalRawClientView": globalRawClientView,
            "globalDataRows": [], 
            "globalHeaders": list(df_payment.columns),
            "globalMinDate": str(df_charge['First Billed Date'].min()),
            "globalMaxDate": str(df_charge['First Billed Date'].max())
        }

        return payload

    except Exception as e:
        return {"error": str(e)}

# Run this locally using: uvicorn main:app --reload