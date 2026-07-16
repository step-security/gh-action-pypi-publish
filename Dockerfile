FROM python:3.13-alpine@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV PIP_NO_CACHE_DIR=1
ENV PIP_ROOT_USER_ACTION=ignore

ENV PATH="/root/.local/bin:${PATH}"
ENV PYTHONPATH="/root/.local/lib/python3.13/site-packages"

RUN apk add --no-cache bash

COPY requirements requirements
RUN \
  PIP_CONSTRAINT=requirements/runtime-prerequisites.txt \
    pip install --user --upgrade --no-cache-dir \
      -r requirements/runtime-prerequisites.in && \
  PIP_CONSTRAINT=requirements/runtime.txt \
    pip install --user --upgrade --no-cache-dir --prefer-binary \
      -r requirements/runtime.in

WORKDIR /app
COPY LICENSE .
COPY twine-upload.sh .
COPY print-hash.py .
COPY print-pkg-names.py .
COPY oidc-exchange.py .
COPY attestations.py .

RUN chmod +x twine-upload.sh
ENTRYPOINT ["/app/twine-upload.sh"]
