FROM python:3.13-slim

WORKDIR /rag

COPY requirements.txt .
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN --mount=type=cache,target=/root/.cache pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "server.server:app", "--host", "0.0.0.0", "--port", "8000"]