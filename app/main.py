from fastapi import FastAPI
from celery.result import AsyncResult
from app.tasks import dummy_task
from app.worker import celery_app

app = FastAPI(
    title="Docivo API", 
    description="Backend engine for heavy PDF processing",
    version="1.0.0"
)

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"status": "Docivo API is running securely!"}

@app.post("/api/v1/test-task/{seconds}")
def trigger_test_task(seconds: int):
    """
    Endpoint to trigger our dummy async task.
    Notice the `.delay()` method - this sends it to the Redis queue!
    """
    task = dummy_task.delay(seconds)
    return {
        "job_id": task.id, 
        "status": "Task dispatched to Celery background worker"
    }

@app.get("/api/v1/jobs/{job_id}")
def get_job_status(job_id: str):
    """
    Endpoint for the Next.js frontend to poll the status of a job.
    """
    task_result = AsyncResult(job_id, app=celery_app)
    
    return {
        "job_id": job_id,
        "status": task_result.status, # e.g., PENDING, STARTED, SUCCESS, FAILURE
        "result": task_result.result if task_result.ready() else None
    }