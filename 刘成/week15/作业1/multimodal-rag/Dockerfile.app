FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml ./

RUN pip install --no-cache-dir -e .

COPY ./app ./app
COPY ./data ./data

ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
