import time
from app.worker import celery_app

@celery_app.task(name="dummy_task")
def dummy_task(seconds: int):
    """
    A simple dummy task to test the Celery queue.
    We will replace this with actual PDF processing logic later.
    """
    # Simulate a heavy CPU task by sleeping
    time.sleep(seconds)
    return {"message": f"Successfully completed a {seconds}-second heavy task!"}