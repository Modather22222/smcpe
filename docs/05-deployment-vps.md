# 05 — Deployment VPS

> This VPS IS production (`/home/projects/smcpe` on Debian 13 trixie). All commands verified 2026-09-14.

## 1) OS + Packages

- Debian 13 trixie
- `cobc 4.0-early-dev`, `nginx 1.26.3`, `sqlite3 3.46.1`, `python 3.14.6`, `ufw 0.36.2`, `fail2ban 1.1.0`
- Install: `apt-get update && apt-get install -y gnucobol4 build-essential nginx python3-venv sqlite3 certbot python3-certbot-nginx ufw fail2ban`

Verify:
```
cobc --version
nginx -v
sqlite3 --version
python3 --version
```

## 2) Firewall & Fail2ban

```
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp
ufw --force enable
ufw status verbose
```

`/etc/fail2ban/jail.local`:
```
[DEFAULT]
bantime=3600
[sshd] enabled=true
[nginx-http-auth] enabled=true
```

Check: `fail2ban-client status` (requires systemd; if container, ensure `service fail2ban start` manually)

## 3) Nginx

Config: `ops/nginx/smcpe.conf` (see file)

- Landing `/` → `root /home/projects/smcpe/landing-page`
- Dashboard `/app/` → `alias /home/projects/smcpe/dashboard/`
- API `/api/` → `proxy_pass http://127.0.0.1:8000` with `limit_req zone=api:10m rate=10r/s`
- Security headers: `X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `Referrer-Policy strict-origin`
- `client_max_body_size 2m`, gzip on

Install:
```
cp ops/nginx/smcpe.conf /etc/nginx/sites-available/smcpe
ln -sf /etc/nginx/sites-available/smcpe /etc/nginx/sites-enabled/smcpe
rm /etc/nginx/sites-enabled/default
nginx -t && nginx -s reload
```

Verify:
```
curl -I http://127.0.0.1/          # 200 + SMCPE landing (6994 bytes)
curl -s http://127.0.0.1/app/ | head # dashboard
cat /var/log/nginx/smcpe-access.log
nginx -T | grep server_name
```

Pending TLS (when domain ready):
```
certbot --nginx -d pay.yourdomain.sd --redirect -m you@company.sd --agree-tos
certbot renew --dry-run
0 3 * * * certbot renew --quiet && systemctl reload nginx
```

## 4) App user & perms

```
mkdir -p /home/projects/smcpe/app/{backend,dashboard,landing-page}
chown -R smcpe:smcpe /home/projects/smcpe/app # if user smcpe exists
chmod 640 backend/db/smcpe.db
chmod 750 backend/db/
```

## 5) Systemd (API)

`ops/systemd/smcpe-api.service` → `/etc/systemd/system/smcpe-api.service`

```
systemctl daemon-reload
systemctl enable --now smcpe-api
systemctl status smcpe-api
journalctl -u smcpe-api -f
curl -s http://127.0.0.1:8000/api/health | jq
```

In container without systemd: start manually `uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --workers 2 &`
