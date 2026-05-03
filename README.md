# 📄 Docivo API - Motor de Procesamiento de Documentos

## 📌 Descripción General

**Docivo** es un servicio backend diseñado para el procesamiento avanzado de documentos PDF y archivos de Office.

Desarrollado sobre un entorno asíncrono utilizando **FastAPI** y **Celery**, permite delegar tareas intensivas como **Reconocimiento Óptico de Caracteres (OCR)** y conversiones de formato a procesos en segundo plano, garantizando una respuesta ágil y escalable de la API.

---

# 🚀 Características Principales

El sistema proporciona múltiples herramientas para la manipulación y transformación de documentos:

### 🖼️ Previsualización de Documentos
Generación de miniaturas e imágenes de alta resolución a partir de archivos PDF.

### 📝 Conversión PDF a Word
Transformación de documentos PDF nativos a formato `.docx` editable.

### 🔍 Procesamiento OCR
Aplicación de reconocimiento óptico de caracteres sobre PDFs escaneados para generar documentos con texto buscable.

### 🤖 OCR Inteligente a Word
Extracción de texto mediante OCR y posterior conversión a formato Word.

### 🖼️ Extracción de Imágenes
Exportación de páginas específicas o completas de un PDF a un archivo comprimido `.zip`.

### 📃 Extracción de Texto Plano
Creación de un nuevo PDF estructurado únicamente con el texto extraído.

### 📄 Conversión Word a PDF
Conversión precisa de archivos `.doc` y `.docx` utilizando LibreOffice en modo headless.

---

# 🏗️ Arquitectura y Tecnologías

## Backend
- **FastAPI** (Python 3.11)

## Procesamiento Asíncrono
- **Celery**

## Broker y Backend de Resultados
- **Redis**

## Librerías de Procesamiento

### 📚 PDFs
- **PyMuPDF (fitz)**  
Manipulación y renderizado veloz de documentos PDF.

### 🔠 OCR
- **pytesseract**
- **Tesseract OCR**

### 🔄 Conversión PDF → Word
- **pdf2docx**

### 🖥️ Conversión Office → PDF
- **LibreOffice (headless)**

## Infraestructura
- **Docker**
- **Docker Compose**

---

# 📋 Requisitos Previos

Asegúrese de tener instalado:

- Docker
- Docker Compose

---

# ⚙️ Instalación y Despliegue

## 1️⃣ Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd docivo-api
```

---

## 2️⃣ Construir y levantar servicios

Ejecute el siguiente comando en la raíz del proyecto:

```bash
docker-compose up --build -d
```

---

## 3️⃣ Servicios levantados

Este comando iniciará:

| Servicio | Descripción |
|---------|-------------|
| **redis** | Instancia Redis para cola de tareas |
| **api** | Servidor FastAPI en puerto `8000` |
| **worker** | Worker Celery para procesamiento |

---

## 4️⃣ Verificación

Acceda a:

```text
http://localhost:8000/
```

Respuesta esperada:

```json
{
  "status": "¡La API de Docivo está funcionando!"
}
```

---

# 🔄 Flujo de Trabajo Asíncrono

Debido a que el procesamiento documental requiere uso intensivo de CPU, Docivo utiliza un flujo basado en **job_id**.

---

## 1️⃣ Iniciar un Trabajo

Enviar una petición `POST` al endpoint deseado con archivo adjunto (`multipart/form-data`).

### Ejemplo

```http
POST /api/v1/tools/pdf-to-word
```

### Respuesta

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

---

## 2️⃣ Consultar Estado

```http
GET /api/v1/jobs/{job_id}
```

### Estados posibles

- `PENDING`
- `STARTED`
- `SUCCESS`
- `FAILURE`

---

## 3️⃣ Descargar Resultado

Una vez completado:

```http
GET /api/v1/downloads/{job_id}
```

El sistema detectará automáticamente el archivo generado y retornará el recurso binario.

---

# 📡 Endpoints Disponibles

---

## 🖥️ Sistema

### Estado del servicio

```http
GET /
```

---

### Consultar estado de tarea

```http
GET /api/v1/jobs/{job_id}
```

---

### Descargar resultado

```http
GET /api/v1/downloads/{job_id}
```

---

# 🛠️ Herramientas de Procesamiento

> Todos requieren método `POST` con archivo en formato `multipart/form-data`

---

## Previsualización

```http
POST /api/v1/tools/preview
```

**Entrada:** `.pdf`  
**Salida:** URLs estáticas de previsualización

---

## PDF → Word

```http
POST /api/v1/tools/pdf-to-word
```

**Entrada:** `.pdf`  
**Salida:** `.docx`

---

## OCR sobre PDF

```http
POST /api/v1/tools/ocr
```

**Entrada:** `.pdf`  
**Salida:** `.pdf` con OCR aplicado

---

## OCR → Word

```http
POST /api/v1/tools/ocr-to-word
```

**Entrada:** `.pdf`  
**Salida:** `.docx`

---

## PDF → Imágenes

```http
POST /api/v1/tools/pdf-to-images
```

**Entrada:** `.pdf`

Parámetro opcional:

```text
pages=all
```

o

```text
pages=0,1,2
```

**Salida:** `.zip`

---

## Extraer Texto a PDF

```http
POST /api/v1/tools/extract-text-pdf
```

**Entrada:** `.pdf`  
**Salida:** `.pdf`

---

## Word → PDF

```http
POST /api/v1/tools/word-to-pdf
```

**Entrada:** `.doc` / `.docx`  
**Salida:** `.pdf`

---

# 📁 Estructura del Proyecto

```text
/app
 ├── main.py
 ├── tasks.py
 ├── worker.py
 └── core/
      └── paths.py

/storage
 ├── uploads/
 └── processed/

Dockerfile
docker-compose.yml
```

---

## Descripción de Archivos

| Archivo | Función |
|--------|---------|
| `main.py` | Definición de endpoints FastAPI |
| `tasks.py` | Lógica de negocio y tareas Celery |
| `worker.py` | Configuración del worker |
| `core/paths.py` | Rutas absolutas de almacenamiento |

---

# 💾 Sistema de Almacenamiento

## `/uploads`
Archivos temporales cargados por usuarios.

## `/processed`
Resultados finales generados por workers.

---

# 🎯 Casos de Uso

Docivo está pensado para:

- Plataformas de gestión documental
- Automatización empresarial
- Digitalización de archivos físicos
- Procesamiento masivo de PDFs
- Conversión de documentos en pipelines automatizados

---

# 📜 Licencia

Este proyecto está bajo la licencia correspondiente definida por el repositorio.

---

# 👨‍💻 Autor

**Docivo API**  
Motor de procesamiento documental asíncrono construido para alto rendimiento y escalabilidad.
