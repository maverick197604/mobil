"""
CAD Viewer Backend — FastAPI application.

Endpoints:
  POST   /api/upload            Upload a CAD file
  GET    /api/convert/{file_id} Convert file to STL and stream it
  GET    /api/files             List uploaded files
  DELETE /api/files/{file_id}   Delete a file

Static frontend is served from /app/static at the root path.
"""

import os
import uuid
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime

import aiofiles
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from freecad_service import convert_to_stl

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/uploads"))
STATIC_DIR = Path(os.getenv("STATIC_DIR", "/app/static"))
METADATA_FILE = UPLOAD_DIR / ".metadata.json"

ALLOWED_EXTENSIONS = {".fcstd", ".step", ".stp", ".iges", ".igs", ".stl"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="CAD Viewer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist at startup
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Metadata helpers
# ---------------------------------------------------------------------------


def _load_metadata() -> dict:
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_metadata(meta: dict) -> None:
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CAD file. Returns a file_id for subsequent operations."""
    original_name = file.filename or "upload"
    suffix = Path(original_name).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Nicht unterstütztes Dateiformat: '{suffix}'. "
                f"Erlaubt: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    file_id = str(uuid.uuid4())
    dest_path = UPLOAD_DIR / f"{file_id}{suffix}"

    try:
        async with aiofiles.open(dest_path, "wb") as out:
            while chunk := await file.read(1024 * 1024):  # 1 MB chunks
                await out.write(chunk)
    except Exception as exc:
        logger.exception("Fehler beim Speichern der Datei: %s", exc)
        raise HTTPException(status_code=500, detail="Datei konnte nicht gespeichert werden.")

    # Persist metadata
    meta = _load_metadata()
    meta[file_id] = {
        "file_id": file_id,
        "original_name": original_name,
        "suffix": suffix,
        "size": dest_path.stat().st_size,
        "uploaded_at": datetime.utcnow().isoformat() + "Z",
        "path": str(dest_path),
    }
    _save_metadata(meta)

    logger.info("Datei hochgeladen: %s → %s", original_name, file_id)
    return {
        "file_id": file_id,
        "original_name": original_name,
        "size": meta[file_id]["size"],
        "uploaded_at": meta[file_id]["uploaded_at"],
    }


@app.get("/api/convert/{file_id}")
def convert_file(file_id: str):
    """Convert the uploaded file to STL and return it as binary content."""
    meta = _load_metadata()
    if file_id not in meta:
        raise HTTPException(status_code=404, detail="Datei nicht gefunden.")

    entry = meta[file_id]
    input_path = Path(entry["path"])
    if not input_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Die Quelldatei wurde auf dem Server nicht gefunden.",
        )

    output_path = UPLOAD_DIR / f"{file_id}.stl"

    # Use cached STL if already converted
    if not output_path.exists():
        result = convert_to_stl(str(input_path), str(output_path))
        if not result["success"]:
            raise HTTPException(status_code=422, detail=result["message"])

    return FileResponse(
        path=str(output_path),
        media_type="model/stl",
        filename=f"{Path(entry['original_name']).stem}.stl",
    )


@app.get("/api/files")
def list_files():
    """Return a list of all uploaded files with metadata."""
    meta = _load_metadata()
    files = []
    for entry in meta.values():
        # Only return files that still exist on disk
        if Path(entry["path"]).exists():
            files.append(
                {
                    "file_id": entry["file_id"],
                    "original_name": entry["original_name"],
                    "suffix": entry["suffix"],
                    "size": entry["size"],
                    "uploaded_at": entry["uploaded_at"],
                }
            )
    # Sort newest first
    files.sort(key=lambda x: x["uploaded_at"], reverse=True)
    return files


@app.delete("/api/files/{file_id}")
def delete_file(file_id: str):
    """Delete an uploaded file and its cached STL conversion."""
    meta = _load_metadata()
    if file_id not in meta:
        raise HTTPException(status_code=404, detail="Datei nicht gefunden.")

    entry = meta[file_id]

    # Remove original file
    original = Path(entry["path"])
    if original.exists():
        original.unlink()

    # Remove cached STL if present
    stl_cache = UPLOAD_DIR / f"{file_id}.stl"
    if stl_cache.exists():
        stl_cache.unlink()

    del meta[file_id]
    _save_metadata(meta)

    logger.info("Datei gelöscht: %s", file_id)
    return {"detail": "Datei erfolgreich gelöscht."}


# ---------------------------------------------------------------------------
# Frontend static files (mount last so API routes take priority)
# ---------------------------------------------------------------------------

if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:
    logger.warning("Frontend-Verzeichnis nicht gefunden: %s", STATIC_DIR)


# ---------------------------------------------------------------------------
# Entry point for local development
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
