"""
Buddensiek PDF Server
=====================
FastAPI server that converts HTML to PDF using Playwright (Chromium).

Endpoint:
    POST /create-pdf
    Body: {"html": "<html>...</html>", "filename": "optional.pdf"}
    Returns: application/pdf binary

Health check:
    GET /
    Returns: {"status": "ok"}
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from playwright.async_api import async_playwright
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("pdf-server")

# Globaler Browser, der einmal beim Start gestartet wird
# (schneller als pro Request einen neuen zu starten)
browser = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Browser beim Start hochfahren, beim Stop sauber schließen."""
    global browser
    log.info("Starting Playwright + Chromium…")
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
        ]
    )
    log.info("Browser ready.")
    yield
    log.info("Shutting down browser…")
    await browser.close()
    await playwright.stop()


app = FastAPI(title="Buddensiek PDF Server", lifespan=lifespan)


class PdfRequest(BaseModel):
    html: str
    filename: str | None = "document.pdf"


@app.get("/")
async def health():
    """Health check / Wake-up endpoint."""
    return {"status": "ok", "service": "buddensiek-pdf-server"}


@app.post("/create-pdf")
async def create_pdf(req: PdfRequest):
    """
    Convert HTML to PDF.

    Request body:
        html (str):     Vollständiges HTML-Dokument
        filename (str): Optional, default "document.pdf"

    Response:
        application/pdf binary mit Content-Disposition Header
    """
    if not req.html or len(req.html.strip()) == 0:
        raise HTTPException(status_code=400, detail="html field is empty")

    log.info(f"Generating PDF: {req.filename} ({len(req.html)} chars)")

    try:
        page = await browser.new_page()

        # HTML laden, auf Network-Idle warten (für Google Fonts etc.)
        await page.set_content(req.html, wait_until="networkidle", timeout=60000)

        # PDF generieren - A4, Hintergrundfarben/Bilder mit drucken
        pdf_bytes = await page.pdf(
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            prefer_css_page_size=True,
        )

        await page.close()

        log.info(f"PDF generated: {len(pdf_bytes)} bytes")

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{req.filename}"',
            },
        )

    except Exception as e:
        log.exception(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
