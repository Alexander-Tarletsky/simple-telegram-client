FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # poetry
    POETRY_VERSION=2.0.3 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # do not ask any interactive question
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN apt-get update
RUN pip3 install --upgrade pip && \
    pip3 install --user pipx && \
    pipx ensurepath && \
    pipx install poetry ${POETRY_VERSION}

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./

# install dependencies
RUN RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

COPY app/main.py ./

RUN poetry install --without dev

# run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]