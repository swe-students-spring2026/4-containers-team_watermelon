FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv install --system --deploy

COPY . .

CMD ["python", "-m", "app.worker"]