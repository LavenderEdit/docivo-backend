from pathlib import Path

# Obtener la ruta base absoluta del proyecto (/code dentro de Docker)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Definir las carpetas de almacenamiento
UPLOAD_DIR = BASE_DIR / "storage" / "uploads"
PROCESSED_DIR = BASE_DIR / "storage" / "processed"

# Asegurar que las carpetas existan en el sistema
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)