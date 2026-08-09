FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    g++ \
    libpq-dev \
    pybind11-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cpp-engine /app/cpp-engine
WORKDIR /app/cpp-engine
RUN mkdir build && cd build && cmake .. && make || true

WORKDIR /app
COPY backend /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
