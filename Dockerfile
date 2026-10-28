FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

FROM base AS web
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py banco.py cliente_api.py categorias.py dados.py ./
COPY .streamlit/ .streamlit/
CMD ["sh", "-c", "streamlit run app.py --server.address 0.0.0.0 --server.port ${PORT:-8501} --server.headless true"]

FROM base AS api
COPY requirements_api.txt ./
RUN pip install --no-cache-dir -r requirements_api.txt
COPY api.py categorias.py dados.py ./
CMD ["sh", "-c", "exec uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}"]
