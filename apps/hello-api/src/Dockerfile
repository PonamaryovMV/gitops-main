# hello-api — только stdlib, зависимостей нет
FROM python:3.14-slim

ARG APP_VERSION=0.0.0
ARG APP_COLOR=blue
ARG APP_BROKEN=false

LABEL org.opencontainers.image.title="hello-api" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.source="https://github.com/PonamaryovMV/gitops-main"

ENV APP_VERSION=${APP_VERSION} \
    APP_COLOR=${APP_COLOR} \
    APP_BROKEN=${APP_BROKEN} \
    PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY app.py .

USER 10001
EXPOSE 8080
CMD ["python", "app.py"]
