import os
import shutil
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from celery import Celery
from celery.result import AsyncResult

app = FastAPI(title="COVID-19 Variant Analysis API")

# Configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/data/uploads")
AGGREGATES_DIR = os.getenv("AGGREGATES_DIR", "/app/data/aggregates")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(AGGREGATES_DIR, exist_ok=True)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Celery Client Setup
celery_client = Celery(
    "backend",
    broker=REDIS_URL,
    backend=REDIS_URL
)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "COVID-19 Variant Analysis API is running"}

@app.post("/upload")
async def upload_sequence(file: UploadFile = File(...)):
    """
    Handle FASTA file upload and trigger analysis task.
    """
    if not file.filename.endswith(('.fasta', '.fa')):
        raise HTTPException(status_code=400, detail="Only FASTA files are allowed (.fasta, .fa)")

    # Generate unique ID for this upload
    upload_id = str(uuid.uuid4())
    safe_filename = f"{upload_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    # Trigger Celery Task
    # We use send_task by name since the worker code is not available in the backend container
    task = celery_client.send_task(
        "worker.tasks.analyze_sequence",
        args=[file_path],
        task_id=upload_id  # Reusing upload_id as task_id for simplicity
    )

    return {
        "task_id": task.id,
        "filename": file.filename,
        "message": "File uploaded successfully, analysis started."
    }

@app.get("/results/{task_id}")
async def get_result(task_id: str):
    """
    Check the status and result of an analysis task.
    """
    result = AsyncResult(task_id, app=celery_client)
    
    response = {
        "task_id": task_id,
        "status": result.state,
    }

    if result.state == 'PENDING':
        response["progress"] = 0
    elif result.state == 'STARTED':
        # Expecting the worker to update state with meta={'progress': ...}
        info = result.info
        if isinstance(info, dict):
            response["progress"] = info.get('progress', 0)
    elif result.state == 'SUCCESS':
        response["progress"] = 100
        response["result"] = result.result
    elif result.state == 'FAILURE':
        response["error"] = str(result.result)

    return response

@app.get("/aggregates/{filename}")
async def get_aggregate_data(filename: str):
    """
    Serve pre-computed aggregate data files (JSON/Parquet).
    """
    # Basic security check to prevent directory traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = os.path.join(AGGREGATES_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Data file not found")
    
    return FileResponse(file_path)
