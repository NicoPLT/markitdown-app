FROM python:3.12-slim

# ffmpeg serve a MarkItDown per la trascrizione dei file audio.
# Le restanti dipendenze di sistema sono già incluse nell'immagine slim.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 7860

# Koyeb passa la porta tramite la variabile $PORT.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
