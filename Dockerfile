FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app

# Normalize CRLF -> LF for Windows commits; make script executable
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

ENV PORT=10000
CMD ["/app/start.sh"]
