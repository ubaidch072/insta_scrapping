# Match Playwright Python package & browser binaries
FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

WORKDIR /app

# Copy deps and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium) and OS deps into the image
RUN playwright install --with-deps chromium

# Copy project files
COPY . .

# Environment: Render exposes a PORT, default to 10000
ENV PORT=10000

# Start FastAPI via Uvicorn
CMD ["uvicorn", "app.webapi:app", "--host", "0.0.0.0", "--port", "10000"]
