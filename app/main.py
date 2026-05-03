import uuid
import shutil
import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from celery.result import AsyncResult

from app.tasks import (
    dummy_task, 
    pdf_to_word_task, 
    generate_preview_task, 
    ocr_pdf_task, 
    ocr_to_word_task,
    pdf_to_images_task,
    extract_text_to_pdf_task,
    word_to_pdf_task
)
from app.worker import celery_app
from app.core.paths import UPLOAD_DIR, PROCESSED_DIR

app = FastAPI(
    title="Docivo API", 
    description="Motor backend para procesamiento avanzado de PDF",
    version="2.0.0"
)

app.mount("/api/v1/static", StaticFiles(directory=PROCESSED_DIR), name="static")

@app.get("/")
def read_root():
    return {"status": "¡La API de Docivo está funcionando!"}

@app.get("/api/v1/jobs/{job_id}")
def get_job_status(job_id: str):
    task_result = AsyncResult(job_id, app=celery_app)
    return {
        "job_id": job_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }

@app.get("/api/v1/downloads/{job_id}")
def download_processed_file(job_id: str):
    task_result = AsyncResult(job_id, app=celery_app)
    if task_result.status != "SUCCESS":
        raise HTTPException(status_code=400, detail="El archivo aún no está listo o falló.")
    
    # Busca dinámicamente cualquier extensión generada (.docx, .pdf, .zip)
    matching_files = list(PROCESSED_DIR.glob(f"{job_id}*.*"))
    if not matching_files:
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el disco.")
        
    output_path = matching_files[0]
    return FileResponse(
        path=output_path, 
        filename=f"Docivo_Procesado{output_path.suffix}",
    )

@app.post("/api/v1/tools/preview")
async def create_pdf_preview(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")
    job_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{job_id}.pdf"
    output_folder = PROCESSED_DIR / job_id 
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    task = generate_preview_task.apply_async(args=[str(input_path), job_id, str(output_folder)], task_id=job_id)
    return {"job_id": task.id, "message": "Generando súper-previsualización."}

@app.post("/api/v1/tools/pdf-to-word")
async def convert_pdf_to_word(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{job_id}.pdf"
    output_path = PROCESSED_DIR / f"{job_id}.docx"
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    task = pdf_to_word_task.apply_async(args=[str(input_path), str(output_path)], task_id=job_id)
    return {"job_id": task.id}

@app.post("/api/v1/tools/ocr")
async def process_ocr(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{job_id}.pdf"
    output_path = PROCESSED_DIR / f"{job_id}_ocr.pdf"
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    task = ocr_pdf_task.apply_async(args=[str(input_path), str(output_path)], task_id=job_id)
    return {"job_id": task.id}

@app.post("/api/v1/tools/ocr-to-word")
async def process_ocr_to_word(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{job_id}.pdf"
    temp_path = PROCESSED_DIR / f"{job_id}_temp.pdf"
    output_path = PROCESSED_DIR / f"{job_id}.docx"
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    task = ocr_to_word_task.apply_async(args=[str(input_path), str(output_path), str(temp_path)], task_id=job_id)
    return {"job_id": task.id}

@app.post("/api/v1/tools/pdf-to-images")
async def convert_pdf_to_images(
    file: UploadFile = File(...), 
    pages: str = Form("all")
):
    job_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{job_id}.pdf"
    output_path = PROCESSED_DIR / f"{job_id}.zip"
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    task = pdf_to_images_task.apply_async(args=[str(input_path), str(output_path), pages], task_id=job_id)
    return {"job_id": task.id, "message": "Procesando imágenes en segundo plano"}

@app.post("/api/v1/tools/extract-text-pdf")
async def extract_text_to_pdf(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{job_id}.pdf"
    output_path = PROCESSED_DIR / f"{job_id}_text_only.pdf"
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    task = extract_text_to_pdf_task.apply_async(args=[str(input_path), str(output_path)], task_id=job_id)
    return {"job_id": task.id, "message": "Extrayendo texto limpio"}

@app.post("/api/v1/tools/word-to-pdf")
async def convert_word_to_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.docx') and not file.filename.endswith('.doc'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un documento Word (.docx o .doc)")

    job_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{job_id}{os.path.splitext(file.filename)[1]}"
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    task = word_to_pdf_task.apply_async(args=[str(input_path), str(PROCESSED_DIR)], task_id=job_id)
    return {"job_id": task.id, "message": "Convirtiendo documento de Office a PDF"}