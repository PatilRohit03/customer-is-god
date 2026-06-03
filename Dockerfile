FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libxcb1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY ./src ./src

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
