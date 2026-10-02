FROM python:3.14-slim
WORKDIR /srv
COPY . .
CMD ["sh", "-c", "exec python -m http.server ${FRONTEND_PORT}"]