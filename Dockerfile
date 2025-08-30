# Playwright + Python base (Chromium ready)
FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

# Saaf logs
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# Playwright browser path
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
# Default port (Render $PORT de deta hai)
ENV PORT=10000 UVICORN_WORKERS=1

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Chromium + deps
RUN playwright install --with-deps chromium

# App code
COPY . .

# Start script permissions
RUN chmod +x /app/start.sh

EXPOSE 10000
CMD ["/app/start.sh"]
