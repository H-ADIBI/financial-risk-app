FROM python:3.11-slim

WORKDIR /app

# System deps kept minimal; add build-essential here if a future
# dependency (e.g. statsmodels for ARIMAX) needs to compile anything.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8000 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

EXPOSE 8000

# GROQ_API_KEY must be supplied at runtime (Azure App Setting / Container App
# secret) -- it is intentionally not baked into the image.
CMD ["streamlit", "run", "app/Home.py", "--server.port=8000", "--server.address=0.0.0.0"]
