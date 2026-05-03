import time
from app.worker import celery_app
from pdf2docx import Converter

@celery_app.task(name="dummy_task")
def dummy_task(seconds: int):
    """Tarea de prueba original."""
    time.sleep(seconds)
    return {"message": f"¡Tarea pesada de {seconds} segundos completada!"}

@celery_app.task(name="pdf_to_word_task")
def pdf_to_word_task(input_path: str, output_path: str):
    """
    Convierte un archivo PDF a un documento de Word (.docx).
    Esta es una tarea intensiva en CPU que correrá en tu procesador i9.
    """
    try:
        cv = Converter(input_path)
        
        cv.convert(output_path, start=0, end=None)
        cv.close()
        
        return {
            "status": "success", 
            "message": "PDF convertido a Word con éxito."
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Fallo en la conversión: {str(e)}"
        }