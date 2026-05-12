FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Устанавливаем порт по умолчанию
ENV PORT=8501

# Открываем переменный порт
EXPOSE $PORT

HEALTHCHECK CMD curl --fail http://localhost:$PORT/_stcore/health || exit 1
ENTRYPOINT ["sh", "-c", "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0"]