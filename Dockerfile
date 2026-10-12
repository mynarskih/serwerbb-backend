FROM python:3.13-alpine

WORKDIR /app
COPY app.py /app/app.py
RUN python -m py_compile /app/app.py \
    && mkdir -p /data \
    && chown 65534:65534 /data

USER 65534:65534
EXPOSE 8080

CMD ["python", "/app/app.py"]
