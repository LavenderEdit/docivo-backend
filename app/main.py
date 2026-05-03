import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from celery.result import AsyncResult

from app.tasks import dummy_task, pdf_to_word_task
from app.worker import celery_app
from app.core.paths import UPLOAD_DIR, PROCESSED_DIR

app = FastAPI(
    title="Docivo API", 
    description="Motor backend para procesamiento pesado de PDF",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"status": "¡La API de Docivo está funcionando!"}

@app.post("/api/v1/tools/pdf-to-word")
async def convert_pdf_to_word(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")

    job_id = str(uuid.uuid4())
    input_filename = f"{job_id}.pdf"
    output_filename = f"{job_id}.docx"
    
    input_path = UPLOAD_DIR / input_filename
    output_path = PROCESSED_DIR / output_filename

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    task = pdf_to_word_task.apply_async(
        args=[str(input_path), str(output_path)], 
        task_id=job_id
    )

    return {
        "job_id": task.id,
        "message": "Archivo subido. Procesamiento en segundo plano iniciado."
    }

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
    
    output_path = PROCESSED_DIR / f"{job_id}.docx"
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el disco.")
        
    return FileResponse(
        path=output_path, 
        filename="Docivo_Convertido.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )