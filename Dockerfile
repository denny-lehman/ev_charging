FROM python:3.11-slim as build

RUN apt-get update \
  && apt-get install -y \
      curl \
	  build-essential \ 
	  libffi-dev \ 
  && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH /root/.local/bin:$PATH

WORKDIR /app
RUN python -m venv --copies /app/venv
COPY pyproject.toml poetry.lock ./
RUN . /app/venv/bin/activate && poetry install --only main

FROM python:3.11-slim as application
COPY --from=build /app/venv /app/venv/

ENV PATH /app/venv/bin:$PATH
WORKDIR /app
COPY . ./
EXPOSE 8501


HEALTHCHECK --interval=30s --timeout=6s \
  CMD curl http://localhost:8501/_stcore/health || exit 1

  CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true", "--server.enableCORS=false", "--server.enableWebsocketCompression=false"]