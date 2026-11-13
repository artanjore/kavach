FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt "psycopg[binary]>=3.2"
COPY app ./app
COPY data ./data
ENV PORT=8000
# KAVACH_ENV=dev turns on the /demo prototype (fake data, no real WhatsApp). Use prod for real users.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
