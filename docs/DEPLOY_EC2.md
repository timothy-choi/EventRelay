# Deploy EventRelay on One EC2 Instance

This guide deploys EventRelay on a single Ubuntu EC2 instance with Docker Compose, Caddy, and free sslip.io hostnames:

- Frontend: `https://eventrelay.<EC2-IP-WITH-DASHES>.sslip.io`
- API: `https://api.eventrelay.<EC2-IP-WITH-DASHES>.sslip.io`

Caddy can issue automatic HTTPS certificates only after these hostnames resolve to the EC2 public IP and inbound ports `80` and `443` are open.

## 1. Launch Ubuntu EC2

1. Create an Ubuntu Server EC2 instance.
2. Choose an instance size with enough memory for the full Docker stack. `t3.small` or larger is a practical starting point.
3. Create or select an SSH key pair.
4. Note the public IPv4 address. The examples below use `1.2.3.4`.

## 2. Open Security Group Ports

Allow inbound traffic:

- `22/tcp` from your IP for SSH
- `80/tcp` from `0.0.0.0/0` for Caddy HTTP validation and redirects
- `443/tcp` from `0.0.0.0/0` for HTTPS

Do not open Postgres, Redis, backend, frontend, or proxy ports publicly. In production Compose, only Caddy publishes host ports.

## 3. Install Docker and Compose

SSH into the instance:

```bash
ssh -i /path/to/key.pem ubuntu@1.2.3.4
```

Install Docker Engine and the Compose plugin:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
```

Log out and back in so the `docker` group membership applies, then verify:

```bash
docker --version
docker compose version
```

## 4. Clone the Repo

```bash
git clone <your-repo-url> EventRelay
cd EventRelay
```

## 5. Generate the Caddyfile

Set the EC2 public IP and render the sslip.io hostnames:

```bash
export EC2_PUBLIC_IP=1.2.3.4
./scripts/render_caddyfile.sh
```

For `1.2.3.4`, the script generates:

- `https://eventrelay.1-2-3-4.sslip.io`
- `https://api.eventrelay.1-2-3-4.sslip.io`

It writes `Caddyfile` from `Caddyfile.template`.

## 6. Create `.env`

Copy the example:

```bash
cp .env.example .env
```

Edit `.env` and replace `<ip-dashed>` with the dashed EC2 IP:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/eventrelay
REDIS_URL=redis://redis:6379/0
USE_NETWORK_PROXY=true
NETWORK_PROXY_URL=http://proxy:8080/proxy
PUBLIC_BASE_URL=https://api.eventrelay.1-2-3-4.sslip.io
NEXT_PUBLIC_API_URL=https://api.eventrelay.1-2-3-4.sslip.io
```

`PUBLIC_BASE_URL` controls built-in receiver URLs returned by the API. `NEXT_PUBLIC_API_URL` controls the frontend server routes that proxy dashboard requests to the API.

## 7. Start Production Compose

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Check the stack:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs caddy --tail=100
```

If Caddy cannot get certificates, confirm that the sslip.io domains resolve to the EC2 public IP and the security group allows inbound `80` and `443`.

## 8. Verify Backend Health

```bash
curl -fsS https://api.eventrelay.1-2-3-4.sslip.io/health
```

Expected response:

```json
{"status":"ok"}
```

## 9. Verify Frontend

Open:

```text
https://eventrelay.1-2-3-4.sslip.io
```

Or check from the terminal:

```bash
curl -I https://eventrelay.1-2-3-4.sslip.io
```

## 10. Run Smoke Test Against EC2

```bash
START_COMPOSE=false \
API_BASE_URL=https://api.eventrelay.1-2-3-4.sslip.io \
FRONTEND_BASE_URL=https://eventrelay.1-2-3-4.sslip.io \
./scripts/full_app_smoke_test.sh
```

The smoke test checks:

- backend `/health`
- frontend HTTP `200`
- built-in test webhook receiver creation
- endpoint creation targeting that receiver
- event creation
- delivery polling until success
- receiver captured the delivered request

## Useful Operations

View logs:

```bash
docker compose -f docker-compose.prod.yml logs -f
```

Restart after changes:

```bash
git pull
./scripts/render_caddyfile.sh
docker compose -f docker-compose.prod.yml up -d --build
```

Stop the stack:

```bash
docker compose -f docker-compose.prod.yml down
```

Remove containers and database volume:

```bash
docker compose -f docker-compose.prod.yml down -v
```
