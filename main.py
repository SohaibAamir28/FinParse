import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any

from parser import parse_statement
from reconciler import reconcile_statement
from exporter import export_to_excel

# Create workspace subdirectories for uploads and exports to follow workspace requirements
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI(title="Messy Bank Statement Parser & Reconciliation Engine")

class TransactionItem(BaseModel):
    date: str
    description: str
    debit: float
    credit: float
    balance: float
    raw_row_idx: int

class ReconciliationRequest(BaseModel):
    transactions: List[TransactionItem]

class ExportRequest(BaseModel):
    transactions: List[TransactionItem]
    summary: Dict[str, Any]

@app.post("/api/upload")
async def upload_statement(file: UploadFile = File(...)):
    """
    Accepts PDF or CSV statement file, parses it, executes reconciliation checks,
    and returns parsed rows and mathematical summaries.
    """
    filename = file.filename
    _, ext = os.path.splitext(filename.lower())
    if ext not in ['.pdf', '.csv', '.xlsx']:
        raise HTTPException(status_code=400, detail="Only PDF, CSV, and XLSX file formats are supported.")
        
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")
        
    # Parse file
    try:
        df_parsed = parse_statement(file_path)
    except Exception as e:
        # Clean up file in case of failure
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=422, detail=f"Failed parsing statement: {str(e)}")
        
    # Reconcile parsed dataframe
    try:
        df_reconciled, summary = reconcile_statement(df_parsed)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error in reconciliation processing: {str(e)}")
        
    # Clean up uploaded file since parsing is done
    if os.path.exists(file_path):
        os.remove(file_path)
        
    # Convert DataFrame to JSON serializable list
    transactions_list = df_reconciled.to_dict(orient="records")
    
    return JSONResponse(content={
        "filename": filename,
        "transactions": transactions_list,
        "summary": summary
    })

@app.post("/api/reconcile")
async def recalculate_reconciliation(req: ReconciliationRequest):
    """
    Accepts customized transactions list from user, runs reconciliation checks,
    and returns revised numbers and status.
    """
    import pandas as pd
    
    records = [t.dict() for t in req.transactions]
    df = pd.DataFrame(records)
    
    try:
        df_reconciled, summary = reconcile_statement(df)
        transactions_list = df_reconciled.to_dict(orient="records")
        return JSONResponse(content={
            "transactions": transactions_list,
            "summary": summary
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Re-reconciliation failure: {str(e)}")

@app.post("/api/export")
async def export_excel_sheet(req: ExportRequest):
    """
    Accepts transactions and summaries, creates a formatted Excel spreadsheet,
    and returns a downloadable file link.
    """
    import pandas as pd
    
    records = [t.dict() for t in req.transactions]
    df = pd.DataFrame(records)
    
    unique_export_name = f"reconciled_statement_{uuid.uuid4().hex[:8]}.xlsx"
    export_path = os.path.join(EXPORT_DIR, unique_export_name)
    
    try:
        export_to_excel(df, req.summary, export_path)
        if not os.path.exists(export_path):
            raise HTTPException(status_code=500, detail="Exported Excel sheet file not found after generation.")
            
        return FileResponse(
            path=export_path, 
            filename="reconciled_bank_statement.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Excel export file: {str(e)}")

# Mount static files directory to serve frontend index page
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
