# Mastra Sentinel Security Architecture

Mastra Sentinel enforces zero-trust security postures throughout the DevOps incident response lifecycle.

## Security Layers Matrix

```
       [ External Spikes / Alerts ]
                     │
                     ▼
       ┌───────────────────────────┐
       │     Enkrypt Middleware    │  <-- Intercepts raw logs, encrypts keys
       └─────────────┬─────────────┘
                     ▼
       ┌───────────────────────────┐
       │    FastAPI Auth Guards    │  <-- Verifies JWT Bearer and SRE Roles
       └─────────────┬─────────────┘
                     ▼
       ┌───────────────────────────┐
       │   PostgreSQL / Qdrant     │  <-- Encryption-at-rest & Isolation
       └───────────────────────────┘
```

## 1. Authentication & Role-Based Access Control (RBAC)
* **JWT Access Keys**: All requests are checked by an OAuth2 HTTP Bearer token scheme.
* **Role Enforcements**: 
  * `SRE_ADMIN`: Full operations access. Allowed to trigger workflows, edit runbooks, and manage database states.
  * `SRE_OPERATOR`: Active response access. Allowed to trigger pipelines and execute manual commands.
  * `SRE_VIEWER`: Read-only access to dashboards, reports, and analytics.

## 2. Enkrypt Middleware Abstraction
SRE logs frequently capture environmental secrets (such as API tokens, database connection strings, or application passwords).
The `EnkryptMiddleware` in `app/auth.py` intercept logging inputs:
* **Secret Redaction**: Checks for patterns resembling sensitive keys (e.g. `api_key=`, `password=`, `token=`).
* **In-Transit Payload Encryption**: Ciphers sensitive logging subfields using robust, irreversible cryptographic envelopes before saving to database disks, protecting historical dumps from leak risks.

## 3. Container & Host Hardening
* All Docker containers run as non-root users (`python:3.11-slim`, `nginx:alpine`) to limit host privileges.
* Database connections run in isolated docker networking interfaces, completely closed to public routing gates.
