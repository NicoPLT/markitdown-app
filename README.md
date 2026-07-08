---
title: MarkItDown Converter
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# MarkItDown Converter

Landing page che converte **qualsiasi documento supportato in Markdown**, usando la libreria
[microsoft/markitdown](https://github.com/microsoft/markitdown). Carichi un file, l'app riconosce
da sola il tipo di documento e restituisce il Markdown pulito (titoli, elenchi, tabelle, link…).

- **Backend:** FastAPI + MarkItDown
- **Frontend:** una singola pagina statica (nessun build step)
- **Deploy:** Docker, pronto per Koyeb

---

## Formati supportati

PDF · Word (DOCX) · PowerPoint (PPTX) · Excel (XLSX) · HTML · CSV · JSON · XML ·
EPUB · ZIP (itera sul contenuto) · immagini (metadati EXIF + OCR) · audio (trascrizione) · e altri.

Il riconoscimento del formato è **automatico**: MarkItDown combina l'estensione, il mimetype e
l'analisi del contenuto (magic bytes), quindi l'utente carica e basta.

---

## Struttura del progetto

```
markitdown-app/
├── app/
│   ├── main.py            # API FastAPI (endpoint /api/convert, /health)
│   └── static/
│       └── index.html     # landing page (drag & drop)
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
└── README.md
```

---

## Uso in locale (con Cursor)

1. Apri la cartella `markitdown-app` in Cursor.
2. Crea un ambiente virtuale e installa le dipendenze:

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Avvia il server:

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

4. Apri <http://localhost:8000>.

> Nota: la trascrizione **audio** richiede `ffmpeg` installato sul sistema. È già incluso
> nell'immagine Docker; in locale installalo solo se ti serve quel formato.

---

## Deploy su Hugging Face Spaces (gratuito)

1. Vai su [huggingface.co/new-space](https://huggingface.co/new-space).
2. Scegli un nome, **SDK: Docker**, visibilità pubblica o privata.
3. Crea lo Space, poi collega il repository GitHub esistente:
   - **Settings → Repository → Link to GitHub repo**, oppure
   - aggiungi lo Space come remote git e pusha il codice:

     ```bash
     git remote add space https://huggingface.co/spaces/<tuo-utente>/<nome-space>
     git push space main
     ```

4. Lo Space rileva il `Dockerfile` e i metadati YAML in cima a questo README
   (`sdk: docker`, `app_port: 7860`) e builda automaticamente.
5. Al termine del build, l'app è disponibile su
   `https://<tuo-utente>-<nome-space>.hf.space`.

> Nota: lo Space va in "sleep" dopo un periodo di inattività e si risveglia
> automaticamente alla prima richiesta (qualche secondo di attesa).

---

## Deploy su Koyeb

Koyeb rileva automaticamente il `Dockerfile` e costruisce l'immagine.

1. Crea un repository su GitHub e carica il progetto:

   ```bash
   git init
   git add .
   git commit -m "MarkItDown converter"
   git branch -M main
   git remote add origin https://github.com/<tuo-utente>/<repo>.git
   git push -u origin main
   ```

2. Su [Koyeb](https://app.koyeb.com) → **Create Service** → **GitHub** → seleziona il repository.
3. **Builder:** lascia *Dockerfile* (rilevato in automatico).
4. **Porta / Health check:** porta `8000`, path health check `/health`.
   Koyeb passa la porta tramite la variabile `$PORT`, già gestita nel `Dockerfile`.
5. (Opzionale) **Environment variables:**
   - `MAX_FILE_SIZE_MB` → limite di upload in MB (default `25`).
6. **Deploy.** Al termine ottieni l'URL pubblico `https://<nome>.koyeb.app`.

---

## API

### `POST /api/convert`

`multipart/form-data` con il campo `file`.

**Risposta `200`:**

```json
{
  "filename": "manuale.docx",
  "output_filename": "manuale.md",
  "characters": 1840,
  "markdown": "# Manuale\n..."
}
```

**Errori:** `400` file vuoto · `413` file troppo grande · `415` formato non supportato ·
`422` file danneggiato/protetto.

### `GET /health`

Restituisce `{"status": "ok"}` (usato dall'health check di Koyeb).

---

## Opzionale: OCR e descrizione immagini con LLM

Di default l'app gira in modalità **offline/locale** (`enable_plugins=False`), senza chiamate
esterne. Per estrarre testo dalle immagini dentro i documenti o descrivere le immagini, MarkItDown
può usare un modello LLM. Per attivarlo, modifica l'istanza in `app/main.py`:

```python
from openai import OpenAI
md = MarkItDown(
    enable_plugins=True,
    llm_client=OpenAI(),     # richiede la variabile d'ambiente OPENAI_API_KEY
    llm_model="gpt-4o",
)
```

E aggiungi `openai` (e il plugin `markitdown-ocr`, se vuoi l'OCR) a `requirements.txt`.

---

## Sicurezza

L'endpoint usa `convert_stream()`, l'API consigliata da MarkItDown per input non fidati lato
server. I file vengono elaborati in memoria e non salvati su disco. È comunque presente un limite
di dimensione configurabile (`MAX_FILE_SIZE_MB`).
