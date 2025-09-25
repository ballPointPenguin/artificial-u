# Deployment

## Production Deployment (Docker + nginx-proxy/Let's Encrypt + Ansible)

This guide sketches a pragmatic, production-lean deployment for the Artificial University stack on a single Linux host using Docker and Ansible, integrating with an existing `nginx-proxy` + Let's Encrypt setup. It assumes you already run `nginx-proxy` and its Let's Encrypt companion on the host, issuing certificates automatically based on container env vars.

### TL;DR

- **Containers**: FastAPI API, SolidJS static site (served by Nginx), PostgreSQL, MinIO (+ optional mc bootstrap)
- **Omitted in prod**: Ollama
- **Public entrypoint**: Only the frontend container is public; it reverse-proxies `/api` to the API container over the Docker network.
- **Proxy integration**: Set `VIRTUAL_HOST`, `VIRTUAL_PORT=80`, `LETSENCRYPT_HOST`, `LETSENCRYPT_EMAIL` on the frontend container for automatic TLS.

---

### Architecture choices

- **Frontend**: Build once and serve static assets with Nginx. Do not run the Vite dev server in production.
- **Backend**: Run the FastAPI app under `uvicorn` (or `gunicorn` + `uvicorn.workers.UvicornWorker` if you prefer). This guide uses `uvicorn` for simplicity.
- **Routing**: External traffic hits the public frontend container. The frontend Nginx proxies `/api` to the API container via the internal Docker network. This keeps a single public hostname and aligns with `web/src/api/config.ts` which uses a relative production base URL (`/api`).
- **Alt (two domains)**: If you prefer `app.example.com` and `api.example.com`, you can expose both containers with their own `VIRTUAL_HOST`/`LETSENCRYPT_HOST`. You would then set the SPA production `API_CONFIG` to absolute `https://api.example.com/api` and tighten CORS accordingly.

---

### Backend Dockerfile (FastAPI)

Create `Dockerfile.api` at repo root:

```dockerfile
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (psycopg, build tools as needed)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better caching
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy the application
COPY . .

# Expose API port
EXPOSE 8000

# Healthcheck hits /api/v1/health
HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD curl -fsS http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "artificial_u.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
```

Notes:

- The app already exposes `/api/v1/health` which we use for the container healthcheck.
- You can replace the final `CMD` with gunicorn if desired.

---

### Frontend Dockerfile (SolidJS + Nginx)

Create `web/Dockerfile` (build context is `web/`):

```dockerfile
# Build stage
FROM node:22-alpine AS build
WORKDIR /app
ARG VITE_AUTH0_DOMAIN
ARG VITE_AUTH0_CLIENT_ID
ARG VITE_AUTH0_AUDIENCE
ENV VITE_AUTH0_DOMAIN=${VITE_AUTH0_DOMAIN} \
    VITE_AUTH0_CLIENT_ID=${VITE_AUTH0_CLIENT_ID} \
    VITE_AUTH0_AUDIENCE=${VITE_AUTH0_AUDIENCE}
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && corepack prepare pnpm@10.14.0 --activate
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

# Runtime stage
FROM nginx:alpine
WORKDIR /usr/share/nginx/html
COPY --from=build /app/dist .
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD wget -qO- http://localhost/ >/dev/null || exit 1
CMD ["nginx", "-g", "daemon off;"]
```

Add `web/nginx.conf` to serve the SPA and proxy API to the backend container named `api`:

```nginx
server {
    listen 80;
    server_name _;

    # Serve built assets
    root /usr/share/nginx/html;
    index index.html;

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API to the backend service in the same Docker network
    location /api/ {
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_pass http://api:8000/api/;
    }
}
```

This keeps the SPA and API on the same origin in production, matching `API_CONFIG` which points production to `'/api'`.

---

### Production docker compose

Create `docker-compose.prod.yml` at repo root:

```yaml
version: "3.9"

services:
  db:
    image: postgres:17
    container_name: artificial_u_postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: artificial_u
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    container_name: artificial_u_minio
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minioadmin}
    command: server --console-address ":9001" /data
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  mc:
    image: minio/mc:latest
    container_name: artificial_u_mc
    depends_on:
      - minio
    volumes:
      - ./scripts/mc_setup.sh:/usr/bin/mc_setup.sh
    entrypoint: ["sh", "/usr/bin/mc_setup.sh"]

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: artificial_u_api
    depends_on:
      - db
      - minio
    environment:
      # Database
      DATABASE_URL: ${DATABASE_URL:-postgresql://postgres:postgres@db:5432/artificial_u}
      # Auth0
      AUTH0_DOMAIN: ${AUTH0_DOMAIN}
      AUTH0_AUDIENCE: ${AUTH0_AUDIENCE}
      AUTH0_ALG: RS256
      # Storage (MinIO)
      STORAGE_TYPE: minio
      STORAGE_ENDPOINT_URL: http://minio:9000
      STORAGE_PUBLIC_URL: ${STORAGE_PUBLIC_URL:-http://minio:9000}
      STORAGE_ACCESS_KEY: ${MINIO_ROOT_USER:-minioadmin}
      STORAGE_SECRET_KEY: ${MINIO_ROOT_PASSWORD:-minioadmin}
      STORAGE_REGION: us-east-1
      STORAGE_AUDIO_BUCKET: artificial-u-audio
      STORAGE_LECTURES_BUCKET: artificial-u-lectures
      STORAGE_IMAGES_BUCKET: artificial-u-images
      # App env
      ENV: production
    expose:
      - "8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  web:
    build:
      context: ./web
      dockerfile: Dockerfile
    container_name: artificial_u_web
    depends_on:
      - api
    environment:
      # Integration with nginx-proxy + letsencrypt-companion on the host
      VIRTUAL_HOST: ${PUBLIC_HOST}
      VIRTUAL_PORT: "80"
      LETSENCRYPT_HOST: ${PUBLIC_HOST}
      LETSENCRYPT_EMAIL: ${LETSENCRYPT_EMAIL}
    expose:
      - "80"
    # If your nginx-proxy expects published ports, you can publish 80:80 instead of expose
    # ports:
    #   - "80:80"

volumes:
  postgres_data:
  minio_data:
```

Notes:

- Only `web` is public. `api` is internal and reached via `web`'s Nginx.
- Set `.env.prod` with `PUBLIC_HOST` and `LETSENCRYPT_EMAIL` (see Ansible section).
- Omitted `ollama` in production.

---

### Environment variables

Backend (`api`):

- `DATABASE_URL` e.g. `postgresql://postgres:postgres@db:5432/artificial_u`
- `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`, `AUTH0_ALG=RS256`
- Storage for MinIO: `STORAGE_*` as shown above
- Optional model API keys per your config

Frontend (`web`):

- For the SPA build, ensure `VITE_AUTH0_*` are baked in at build time if using Auth0 login. When building via the multi-stage Dockerfile, inject using build args or a `.env.production` placed in `web/` (Vite reads `VITE_*`). Example build args approach:

```yaml
web:
  build:
    context: .
    dockerfile: web/Dockerfile
    args:
      VITE_AUTH0_DOMAIN: ${VITE_AUTH0_DOMAIN}
      VITE_AUTH0_CLIENT_ID: ${VITE_AUTH0_CLIENT_ID}
      VITE_AUTH0_AUDIENCE: ${VITE_AUTH0_AUDIENCE}
```

Then in `web/Dockerfile` build stage, add `ARG` lines and export to the env before `pnpm build`.

---

### Ansible automation

Create `ansible/deploy.yml` in this repo to provision Docker, pull/build images, create an `.env.prod`, and run Compose. Below is a minimal, idempotent playbook:

```yaml
- name: Deploy ArtificialU
  hosts: artificialu
  become: true
  vars:
    app_dir: /opt/artificial_u
    git_repo: https://github.com/your-org/artificial-u.git
    git_version: main
    # Public DNS for the SPA
    PUBLIC_HOST: app.artificial-u.com
    LETSENCRYPT_EMAIL: you@example.com
    # Backend secrets
    AUTH0_DOMAIN: your-tenant.auth0.com
    AUTH0_AUDIENCE: https://api.artificial-u.com
    DATABASE_URL: postgresql://postgres:postgres@db:5432/artificial_u
    MINIO_ROOT_USER: minioadmin
    MINIO_ROOT_PASSWORD: minioadmin
  tasks:
    - name: Ensure packages present (Docker + Compose plugin)
      ansible.builtin.package:
        name:
          - docker.io
          - docker-compose-plugin
        state: present

    - name: Ensure Docker service running
      ansible.builtin.service:
        name: docker
        state: started
        enabled: true

    - name: Create app directory
      ansible.builtin.file:
        path: "{{ app_dir }}"
        state: directory
        mode: "0755"

    - name: Check out repository
      ansible.builtin.git:
        repo: "{{ git_repo }}"
        dest: "{{ app_dir }}"
        version: "{{ git_version }}"
        force: true

    - name: Write .env.prod for Compose
      ansible.builtin.copy:
        dest: "{{ app_dir }}/.env.prod"
        mode: "0600"
        content: |
          PUBLIC_HOST={{ PUBLIC_HOST }}
          LETSENCRYPT_EMAIL={{ LETSENCRYPT_EMAIL }}
          AUTH0_DOMAIN={{ AUTH0_DOMAIN }}
          AUTH0_AUDIENCE={{ AUTH0_AUDIENCE }}
          DATABASE_URL={{ DATABASE_URL }}
          MINIO_ROOT_USER={{ MINIO_ROOT_USER }}
          MINIO_ROOT_PASSWORD={{ MINIO_ROOT_PASSWORD }}

    - name: Build and start containers
      community.docker.docker_compose_v2:
        project_src: "{{ app_dir }}"
        files:
          - docker-compose.prod.yml
        env_files:
          - .env.prod
        state: present
        build: always
        pull: always

    - name: Run DB migrations (alembic) using the API image
      ansible.builtin.command:
        chdir: "{{ app_dir }}"
        cmd: docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head

    - name: Restart API after migration
      community.docker.docker_compose_v2:
        project_src: "{{ app_dir }}"
        files:
          - docker-compose.prod.yml
        state: restarted
        services:
          - api
```

Inventory example (`ansible/inventory`):

```ini
[artificialu]
your.server.ip.address ansible_user=ubuntu
```

Run:

```bash
ansible-playbook -i ansible/inventory ansible/deploy.yml
```

---

### nginx-proxy / Let's Encrypt notes

- Ensure your host is already running `nginx-proxy` and the `letsencrypt-nginx-proxy-companion`.
- The `web` container must be reachable by `nginx-proxy` (typically by sharing the `nginx-proxy` Docker network). If your proxy uses a dedicated network (e.g., `proxy`), attach `web` and `api` to it:

```yaml
networks:
  proxy:
    external: true

services:
  web:
    networks:
      - default
      - proxy
  api:
    networks:
      - default
      - proxy
```

In this setup, keep only `web` publicly exposed via `VIRTUAL_HOST`. `api` will still be accessible to `web` over the default app network, and optionally accessible to the proxy for advanced routing if needed.

---

### Operational checklist

- **Backups**: Snapshot `postgres_data` and `minio_data` volumes on a schedule.
- **Monitoring**: Container healthchecks are included; add Prometheus/Grafana or external uptime checks as needed.
- **CORS**: Since SPA and API share the same origin in this plan, CORS can be strict in production.
- **Auth0**: Configure Allowed Callback URLs, Logout URLs, and Web Origins per `docs/AUTHENTICATION.md`.
- **Zero-downtime**: Use rolling `docker compose up -d --build` or blue/green (beyond scope here) if the app grows.

---

### FAQ

- **Why not serve the SPA from Python?** Keeping static assets on Nginx is simpler and faster. It also centralizes path-based proxying to the API.
- **Why not expose the API publicly?** You can, but sharing the origin with the SPA simplifies CORS, cookies, and headers.
- **Can I add a CDN later?** Yes—front the `web` container with a CDN that respects `/.well-known` and `/api/*` pass-through.
