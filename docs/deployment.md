# Mastra Sentinel Production Deployment Guide

This document describes how to deploy Mastra Sentinel locally or in enterprise-scale cloud environments.

## Local Multi-Container Deployment

Run the complete four-service stack locally with a single command:

```bash
docker-compose up --build -d
```

This starts:
1. **React Web Frontend** on `http://localhost:3000`
2. **FastAPI core Backend** on `http://localhost:8000`
3. **PostgreSQL database** on `localhost:5432`
4. **Qdrant Vector engine** on `http://localhost:6333`

---

## Production Cloud Run / Kubernetes Deployment

To deploy in cloud environments (such as Google Cloud Run or GKE):

### 1. Database Provisioning
* Deploy a fully managed relational instance (e.g. Google Cloud SQL PostgreSQL).
* Set `DATABASE_URL` inside server configurations to route securely.

### 2. Managed Vector Indexing
* Provision a clustered Qdrant instance.
* Supply `QDRANT_HOST` and `QDRANT_API_KEY` to the SRE core service.

### 3. Container Registries
Build and push images to Google Artifact Registry:

```bash
# Build & Tag Backend
docker build -t gcr.io/my-project/sentinel-backend:latest ./backend
docker push gcr.io/my-project/sentinel-backend:latest

# Build & Tag Frontend
docker build -t gcr.io/my-project/sentinel-frontend:latest .
docker push gcr.io/my-project/sentinel-frontend:latest
```

---

## Environmental Variable Configurations

Ensure these key production settings are locked in the container environment:

* `GEMINI_API_KEY`: High-availability SRE LLM generation token.
* `SECRET_KEY`: Long, secure secret for encoding SRE JWT access keys.
* `POSTGRES_PASSWORD`: Strong password protecting relational databases.
