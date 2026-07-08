# Presence relay — build context is the REPO ROOT:
#   docker build -f presence/relay/Dockerfile .
# The relay imports presence.core.schema, so the package ships whole; its
# runtime deps are only fastapi, uvicorn, pydantic.
FROM python:3.13-slim

WORKDIR /app
RUN pip install --no-cache-dir fastapi==0.139.0 uvicorn==0.51.0 pydantic==2.13.4

COPY presence/ presence/

EXPOSE 8080
CMD ["uvicorn", "presence.relay.app:app", "--host", "0.0.0.0", "--port", "8080"]
