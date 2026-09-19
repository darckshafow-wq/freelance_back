import os
import uuid
from PIL import Image
from fastapi import UploadFile, HTTPException
from typing import Tuple, Optional

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Configuration des tailles selon le type
IMAGE_SIZES = {
    "avatar": (300, 300),
    "project": (1200, 800),
    "thumbnail": (150, 150)
}

def validate_image(file: UploadFile):
    """Vérifie le type MIME et la taille du fichier"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image.")

    # On ne peut pas lire la taille directement sans lire le contenu
    # On le fera pendant la lecture

async def process_and_save_image(file: UploadFile, image_type: str = "project") -> str:
    """Redimensionne et sauvegarde une image localement"""
    validate_image(file)

    # Création du dossier si inexistant
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Lecture du contenu
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="L'image est trop lourde (max 5 Mo).")

    # Génération du nom unique
    ext = "jpg" # On convertit tout en JPG pour uniformiser et optimiser
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        # Traitement d'image avec Pillow
        from io import BytesIO
        img = Image.open(BytesIO(content))

        # Conversion en RGB (pour gérer les PNG avec transparence vers JPG)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Redimensionnement intelligent (maintien du ratio)
        target_size = IMAGE_SIZES.get(image_type, IMAGE_SIZES["project"])
        img.thumbnail(target_size, Image.Resampling.LANCZOS)

        # Sauvegarde optimisée
        img.save(file_path, "JPEG", quality=85, optimize=True)

        return f"/{UPLOAD_DIR}/{filename}"

    except Exception as e:
        print(f"Erreur traitement image: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors du traitement de l'image.")

def delete_old_file(file_url: str):
    """Supprime un ancien fichier du disque"""
    if not file_url:
        return
    path = file_url.lstrip("/")
    if os.path.exists(path):
        try:
            os.remove(path)
        except:
            pass
