
FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PLAYWRIGHT_DISABLE_BROWSER_DOWNLOAD=1
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . /app
RUN chmod +x /app/start.sh || true
EXPOSE 10000
CMD ["/app/start.sh"]
