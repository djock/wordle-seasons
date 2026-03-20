FROM python:3.11.1 as base

ENV VIRTUAL_ENV=/app
RUN python -m venv ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11.1-slim as production

WORKDIR /app

COPY --from=base /app /app/
COPY . .

ENV VIRTUAL_ENV=/app
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

RUN mkdir -p /data

CMD ["python", "-u", "src/app.py"]
