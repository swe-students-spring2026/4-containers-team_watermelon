FROM python:3.10-slim

WORKDIR /app

COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv install --system --deploy

COPY . .

EXPOSE 5001

CMD ["python", "app.py"]