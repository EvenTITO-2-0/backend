FROM python:3.11-slim as base

WORKDIR /code

RUN apt-get update && apt-get install -y git

COPY ./requirements.txt /code/requirements.txt

# -------------------- Development stage --------------------
FROM base as development
COPY ./requirements-dev.txt /code/requirements-dev.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt -r /code/requirements-dev.txt && \
    pip install debugpy && \
    rm -rf /root/.cache /var/lib/apt/lists/* /tmp/*

# Install additional development tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    make \
    && rm -rf /var/lib/apt/lists/*

COPY ./app /code/app
COPY ./assets /code/assets

CMD python -m debugpy --listen 0.0.0.0:5678 -m uvicorn app.main:app --host=0.0.0.0 --port=${PORT} --reload

# -------------------- Production stage --------------------
FROM base as production
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt && \
    rm -rf /root/.cache /var/lib/apt/lists/* /tmp/*

RUN apt-get remove -y git && apt-get autoremove -y

COPY ./app /code/app
COPY ./assets /code/assets

CMD uvicorn app.main:app --host=0.0.0.0 --port=${PORT}
