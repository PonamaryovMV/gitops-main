# Демо-компонент ФП qa/at: один код, имя сервиса/компонента и версия задаются при сборке
FROM python:3.14-slim

ARG APP_SERVICE=unknown
ARG APP_COMPONENT=unknown
ARG APP_VERSION=none

LABEL org.opencontainers.image.source="https://github.com/PonamaryovMV/gitops-main" \
      org.opencontainers.image.title="qa-at-${APP_SERVICE}-${APP_COMPONENT}" \
      org.opencontainers.image.version="${APP_VERSION}"

ENV APP_SERVICE=${APP_SERVICE} \
    APP_COMPONENT=${APP_COMPONENT} \
    APP_VERSION=${APP_VERSION} \
    PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY app.py .

USER 10001
EXPOSE 8080
CMD ["python", "app.py"]
