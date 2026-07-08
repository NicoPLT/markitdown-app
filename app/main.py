"""
MarkItDown Converter — backend FastAPI.

Espone una piccola API che riceve un documento, lo converte in Markdown con la
libreria MarkItDown di Microsoft e restituisce il risultato. Il tipo di file
viene riconosciuto automaticamente da MarkItDown (estensione + analisi del
contenuto/magic bytes), quindi l'utente carica e basta.
"""

import io
import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from markitdown import (
    MarkItDown,
    StreamInfo,
    UnsupportedFormatException,
    FileConversionException,
)

# Dimensione massima accettata per l'upload (in MB). Modificabile da variabile
# d'ambiente su Koyeb senza toccare il codice.
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="MarkItDown Converter",
    description="Carica un documento e ottieni il Markdown. Riconoscimento del formato automatico.",
    version="1.0.0",
)

# Un'unica istanza riutilizzabile. enable_plugins=False per restare nel
# comportamento offline/sicuro di default (vedi README per attivare OCR/LLM).
md = MarkItDown(enable_plugins=False)


@app.get("/health")
def health() -> dict:
    """Endpoint di health-check usato da Koyeb."""
    return {"status": "ok"}


@app.post("/api/convert")
async def convert(file: UploadFile = File(...)) -> JSONResponse:
    """Riceve un file, lo converte in Markdown e restituisce il testo."""
    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="Il file è vuoto.")

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File troppo grande. Limite: {MAX_FILE_SIZE_MB} MB.",
        )

    filename = file.filename or "documento"
    extension = Path(filename).suffix or None

    # Forniamo a MarkItDown tutti gli indizi disponibili (nome, estensione,
    # mimetype): la libreria li combina con l'analisi del contenuto per
    # riconoscere automaticamente il tipo di documento.
    stream_info = StreamInfo(
        filename=filename,
        extension=extension,
        mimetype=file.content_type or None,
    )

    try:
        # convert_stream è l'API raccomandata per input non fidati (server-side).
        result = md.convert_stream(io.BytesIO(contents), stream_info=stream_info)
    except UnsupportedFormatException:
        raise HTTPException(
            status_code=415,
            detail="Formato non supportato. Controlla l'elenco dei formati accettati.",
        )
    except FileConversionException:
        raise HTTPException(
            status_code=422,
            detail="Impossibile convertire il file: potrebbe essere danneggiato o protetto.",
        )
    except Exception as exc:  # pragma: no cover - rete di sicurezza
        raise HTTPException(status_code=500, detail=f"Errore durante la conversione: {exc}")

    markdown = result.text_content or ""
    output_name = Path(filename).stem + ".md"

    return JSONResponse(
        {
            "filename": filename,
            "output_filename": output_name,
            "characters": len(markdown),
            "markdown": markdown,
        }
    )


@app.get("/", response_class=FileResponse)
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
