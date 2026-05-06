# Buddensiek PDF Server

HTML-zu-PDF-Konverter für die Buddensiek Performance Meal-Plan-Automation.

## Stack

- **FastAPI** — Python web framework
- **Playwright (Chromium)** — Headless browser für PDF-Rendering
- **Render** — Deployment-Plattform

## API

### `POST /create-pdf`

**Request:**
```json
{
  "html": "<!DOCTYPE html>...",
  "filename": "Ernaehrungsplan_Max_Muster.pdf"
}
```

**Response:** PDF binary mit `application/pdf` content-type.

### `GET /`

Health check. Antwortet mit `{"status": "ok"}`.

## Deployment auf Render

1. Repo zu GitHub pushen
2. Render Dashboard → New Web Service → Repo verbinden
3. Render erkennt `render.yaml` automatisch
4. Service deployt sich selbst beim ersten Push

Beim Build wird Chromium installiert (~5 Min beim ersten Mal). Danach Cold Start ~30-60s auf Free Tier.

## Lokal testen

```bash
pip install -r requirements.txt
playwright install chromium
python generate_pdf.py
```

Server läuft dann auf `http://localhost:8000`. Test-Request:

```bash
curl -X POST http://localhost:8000/create-pdf \
  -H "Content-Type: application/json" \
  -d '{"html": "<h1>Hallo Welt</h1>", "filename": "test.pdf"}' \
  -o test.pdf
```

## n8n Integration

HTTP Request Node:
- Method: `POST`
- URL: `https://buddensiek-pdf-server.onrender.com/create-pdf`
- Body Type: JSON
- Body:
  ```
  {
    "html": {{ JSON.stringify($json.htmlContent) }},
    "filename": "Ernaehrungsplan_{{ $json.vorname }}_{{ $json.nachname }}.pdf"
  }
  ```
- Response Format: `File`
- Retry on Fail: aktivieren (5 Tries, 15s Wait — wegen Cold Start)
