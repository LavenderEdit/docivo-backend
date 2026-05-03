import time
import os
import io
import zipfile
import re
import subprocess
from PIL import Image
import fitz  # PyMuPDF
import pytesseract
from pdf2docx import Converter

from app.worker import celery_app

def sanitize_docx(docx_path: str):
    temp_docx = docx_path + ".tmp"
    with zipfile.ZipFile(docx_path, 'r') as zin:
        with zipfile.ZipFile(temp_docx, 'w') as zout:
            for item in zin.infolist():
                buffer = zin.read(item.filename)
                if item.filename == 'word/document.xml':
                    text = buffer.decode('utf-8')
                    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)
                    buffer = text.encode('utf-8')
                zout.writestr(item, buffer)
    os.remove(docx_path)
    os.rename(temp_docx, docx_path)

@celery_app.task(name="dummy_task")
def dummy_task(seconds: int):
    time.sleep(seconds)
    return {"message": f"¡Tarea pesada de {seconds} segundos completada!"}

@celery_app.task(name="pdf_to_word_task")
def pdf_to_word_task(input_path: str, output_path: str):
    try:
        cv = Converter(input_path)
        cv.convert(output_path, start=0, end=None)
        cv.close()
        return {"status": "success", "message": "PDF convertido a Word con éxito."}
    except Exception as e:
        return {"status": "error", "message": f"Fallo en la conversión: {str(e)}"}

@celery_app.task(name="generate_preview_task")
def generate_preview_task(input_path: str, job_id: str, output_folder: str):
    try:
        os.makedirs(output_folder, exist_ok=True)
        doc = fitz.open(input_path)
        
        pages_data = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            pix_high = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            img_path = os.path.join(output_folder, f"page_{page_num + 1}.png")
            pix_high.save(img_path)
            
            pix_thumb = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
            thumb_path = os.path.join(output_folder, f"thumb_{page_num + 1}.png")
            pix_thumb.save(thumb_path)
            
            pages_data.append({
                "page": page_num + 1,
                "width": page.rect.width,
                "height": page.rect.height,
                "aspect_ratio": page.rect.width / page.rect.height if page.rect.height else 1,
                "high_res_url": f"/api/v1/static/{job_id}/page_{page_num + 1}.png",
                "thumb_url": f"/api/v1/static/{job_id}/thumb_{page_num + 1}.png",
            })
            
        doc.close()
        return {
            "status": "success", 
            "total_pages": len(pages_data),
            "pages": pages_data
        }
    except Exception as e:
        return {"status": "error", "message": f"Fallo en previsualización: {str(e)}"}

@celery_app.task(name="ocr_pdf_task")
def ocr_pdf_task(input_path: str, output_path: str):
    try:
        doc = fitz.open(input_path)
        output_pdf = fitz.open() 
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf')
            page_doc = fitz.open("pdf", pdf_bytes)
            output_pdf.insert_pdf(page_doc)
            page_doc.close()
        output_pdf.save(output_path)
        output_pdf.close()
        doc.close()
        return {"status": "success", "message": "OCR completado."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@celery_app.task(name="ocr_to_word_task")
def ocr_to_word_task(input_path: str, output_path: str, temp_pdf_path: str):
    try:
        doc = fitz.open(input_path)
        temp_pdf = fitz.open()
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf')
            page_doc = fitz.open("pdf", pdf_bytes)
            temp_pdf.insert_pdf(page_doc)
            page_doc.close()
        temp_pdf.save(temp_pdf_path)
        temp_pdf.close()
        doc.close()
        
        cv = Converter(temp_pdf_path)
        cv.convert(output_path, start=0, end=None)
        cv.close()
        
        sanitize_docx(output_path)
        
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
            
        return {"status": "success", "message": "¡OCR Inteligente a Word completado!"}
    except Exception as e:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
        return {"status": "error", "message": str(e)}

@celery_app.task(name="pdf_to_images_task")
def pdf_to_images_task(input_path: str, output_zip_path: str, pages_to_extract: str):
    try:
        doc = fitz.open(input_path)
        
        if pages_to_extract.lower() == "all":
            pages_list = list(range(len(doc)))
        else:
            pages_list = [int(p) for p in pages_to_extract.split(",") if p.strip().isdigit()]

        with zipfile.ZipFile(output_zip_path, 'w') as zipf:
            for page_num in pages_list:
                if 0 <= page_num < len(doc):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0))
                    img_data = pix.tobytes("png")
                    zipf.writestr(f"pagina_{page_num + 1}.png", img_data)
                    
        doc.close()
        return {"status": "success", "message": "Imágenes extraídas y comprimidas en ZIP."}
    except Exception as e:
        return {"status": "error", "message": f"Fallo al extraer imágenes: {str(e)}"}

@celery_app.task(name="extract_text_to_pdf_task")
def extract_text_to_pdf_task(input_path: str, output_path: str):
    try:
        doc = fitz.open(input_path)
        new_pdf = fitz.open()
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            
            extracted_text = pytesseract.image_to_string(img)
            
            new_page = new_pdf.new_page(width=595, height=842)
            
            rect = fitz.Rect(50, 50, 545, 792) # Márgenes de 50px
            new_page.insert_textbox(rect, extracted_text, fontsize=11, fontname="helv")
            
        new_pdf.save(output_path)
        new_pdf.close()
        doc.close()
        
        return {"status": "success", "message": "Texto extraído y guardado en un nuevo PDF limpio."}
    except Exception as e:
        return {"status": "error", "message": f"Fallo al extraer texto limpio: {str(e)}"}

@celery_app.task(name="word_to_pdf_task")
def word_to_pdf_task(input_path: str, output_dir: str):
    """
    Usa el motor de LibreOffice instalado en Docker para convertir .docx a .pdf
    sin perder el formato original.
    """
    try:
        command = [
            "libreoffice", 
            "--headless", 
            "--convert-to", "pdf", 
            input_path, 
            "--outdir", output_dir
        ]
        
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return {"status": "success", "message": "Documento Word convertido a PDF exitosamente."}
    except Exception as e:
        return {"status": "error", "message": f"Fallo al convertir Word a PDF: {str(e)}"}