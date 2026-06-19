# VM Setup Guide (swe.fm.tul.cz)

This document outlines the one-time setup required on the `swe.fm.tul.cz` server to host the Student Projects Catalogue.

## Prerequisites
*   Docker and Docker Compose installed.
*   PostgreSQL installed and running (standard port 5432).
*   SSH access for the deployment user.

## 1. Directory Structure
Create the following directory structure for the application:
```bash
mkdir -p ~/spc/prod
mkdir -p ~/spc/dev
mkdir -p ~/spc/nginx
mkdir -p ~/spc/otel/prometheus
mkdir -p ~/spc/otel/grafana/provisioning
```

## 2. GitHub Actions Deployment User
1.  Generate an SSH key pair on your local machine:
    ```bash
    ssh-keygen -t ed25519 -C "github-actions-deploy"
    ```
2.  Add the **public key** to `~/.ssh/authorized_keys` on `swe.fm.tul.cz`.
3.  Add the **private key** to your GitHub repository secrets as `SSH_PRIVATE_KEY`.
4.  Add the server host (`swe.fm.tul.cz`) and deployment user as `SSH_HOST` and `SSH_USER` secrets.

## 3. Environment Variables
Create `.env` files in `~/spc/prod` and `~/spc/dev` with the following variables:
*   `DATABASE_URL`: Connection string for the local PostgreSQL.
*   `VITE_API_URL`: Path to the API (e.g., `/api/v1` for prod).
*   `VITE_BASE_URL`: The base path for the app (e.g., `/projects/`).
*   `SECRET_KEY`: JWT signing key.
*   `OTEL_EXPORTER_OTLP_ENDPOINT`: `http://jaeger:4317` (within Docker network).

## 4. Reverse Proxy Initialization
The `nginx.conf` and `docker-compose.yml` will be managed by the CI/CD pipeline, but ensure no other service is occupying port 80/443 on the host.
