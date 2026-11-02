FROM python:3.15-slim@sha256:94d3426f1def7db4a106a232ac121bfd975393e5dfd40a619b955fae45fe7913

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV PIP_NO_CACHE_DIR=1
ENV PIP_ROOT_USER_ACTION=ignore

ENV PATH="/root/.local/bin:${PATH}"
ENV PYTHONPATH="/root/.local/lib/python3.13/site-packages"

COPY .pip-tools.toml .
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
