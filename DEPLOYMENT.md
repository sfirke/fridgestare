# Deploying Fridgestare

This is the single-VM deployment: one small server running three containers behind
Caddy, which terminates TLS, serves the built SPA, and proxies `/api` to the backend.
The app and the API share one origin, which is why the session cookie stays
`SameSite=Lax` and no CORS configuration is needed.

```
        :443
    ┌─────────────┐        ┌──────────┐        ┌────────┐
    │ web (Caddy) │ /api/* │ backend  │        │  db    │
    │ SPA + TLS   ├───────►│ FastAPI  ├───────►│MariaDB │
    └─────────────┘        └──────────┘        └────────┘
      published            internal only        internal only
```

`docker-compose.yml` is the development stack (source mounts, reloaders, database
published to localhost). `docker-compose.prod.yml` is this one. They are separate
files, not overlays; never bring the dev one up on the server.

## 1. Before you touch the server

**Domain.** Buy a domain (or use a subdomain of one you have). You need one A record
— `fridgestare.example.com` → the VM's IPv4 address — and an AAAA record if the VM has
IPv6. Do this first: DNS has to resolve before Caddy can get a certificate.

**Mailgun.** Only needed for the weekly plan email; everything else works without it.

1. Create a Mailgun account and add a sending domain, conventionally a subdomain such
   as `mg.fridgestare.example.com`. A subdomain keeps mail sending from affecting the
   root domain's reputation.
2. Mailgun gives you DNS records to add at your registrar: two TXT records (SPF and
   DKIM), and optionally MX and CNAME records. Add them and wait for Mailgun to show
   the domain as verified — this can take up to a few hours.
3. Copy the domain's **sending API key** (Mailgun's newer keys are per-domain; the
   older account-wide `key-...` private API key also works).
4. Note the region. An EU sending domain needs `MAILGUN_BASE_URL=https://api.eu.mailgun.net`;
   a US one keeps the default. Sending to the wrong region returns 401 on every message.
5. Mailgun free/trial accounts only deliver to *authorized recipients*. Add your own
   address there, or upgrade, or the first weekly email is accepted and then dropped.

**OpenRouter.** Optional. Create a key at openrouter.ai and put some credit on it. It
improves how the planner chat interprets free-text edits; without it the chat falls
back to local keyword parsing. `OPENROUTER_MODEL` defaults to `openai/gpt-4.1-mini`.

**Tavily.** Optional, and the one most people skip. It powers live web-backed recipe
discovery; without a key, discovery returns local suggestions.

## 2. The VM

Any small cloud VM works — 1 vCPU and 2 GB of RAM is comfortable for one household.
2 GB matters more than CPU: MariaDB plus the Python process plus a container build
will fail on a 1 GB box. Give it 20 GB of disk.

```bash
# On a fresh Debian/Ubuntu VM, as a user with sudo:
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
sudo usermod -aG docker "$USER" && newgrp docker

sudo mkdir -p /opt/fridgestare && sudo chown "$USER" /opt/fridgestare
git clone <your-repo-url> /opt/fridgestare
cd /opt/fridgestare
```

Open ports 80 and 443 in the provider's firewall, and 22 for yourself. Port 80 is not
optional: Let's Encrypt validates over it. Nothing else should be reachable — the
database is not published to the host at all in the production stack.

## 3. Configure

```bash
cp .env.production.example .env
openssl rand -base64 48   # APP_SECRET_KEY
openssl rand -base64 24   # MARIADB_PASSWORD
openssl rand -base64 24   # MARIADB_ROOT_PASSWORD
$EDITOR .env
chmod 600 .env
```

Fill in every blank. `DATABASE_URL` has to repeat the password you set in
`MARIADB_PASSWORD` — they are two separate settings that must agree.

The backend refuses to start in `APP_ENV=production` if any of these is wrong, rather
than running in a quietly insecure state:

| Refusal | Why |
| --- | --- |
| `APP_SECRET_KEY` is the example value, or under 32 characters | It signs session cookies; the example value is published in this repo, so anyone could mint a session |
| `APP_BASE_URL` is `http://` | Plan emails link to it and cookies are scoped to it |
| `APP_BASE_URL` is https but `COOKIE_SECURE=false` | The session cookie would also be sent over plain HTTP |
| `SCHEDULER_ENABLED=true` with no Mailgun credentials | The weekly plan would be generated and then thrown away |
| Mailgun configured but `MAIL_FROM_ADDRESS` still ends in `.local` | Mailgun rejects the sender |

If the backend container exits on boot, `docker compose -f docker-compose.prod.yml logs backend`
shows which of these it is.

## 4. Bring it up

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f web     # watch the certificate get issued
```

The backend runs `alembic upgrade head` before it starts serving, so the schema is in
place by the time the first request lands.

Create your account — this is the only way in, there is no public sign-up:

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python -m app.cli.main users create \
  --email you@example.com --password 'a-long-passphrase' \
  --timezone America/New_York --admin
```

Then rotate that password from a prompt rather than leaving it in shell history:

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python -m app.cli.main users set-password --email you@example.com
```

Visit `https://fridgestare.example.com` and log in.

## 5. After first login

In **Preferences**, set the timezone, which weekday the week starts on, and — if you
want the weekly email — turn on email delivery and pick the send weekday and local
time. The scheduler wakes every 30 minutes and sends once that weekday and time have
passed in your timezone, at most once per week's plan.

Before trusting the schedule, send one by hand: open a plan, hit **Preview email**,
then **Send email**. The response says which path it took — `mailgun` means it left the
building, `mock` means Mailgun is not configured. A configured-but-failing Mailgun now
returns an error with Mailgun's own explanation instead of silently pretending to send.

## 6. Backups

The MariaDB volume is the only state worth keeping. Nightly dumps:

```bash
./ops/backup.sh                    # writes ./backups/fridgestare-<timestamp>.sql.gz
crontab -e
# 0 3 * * * cd /opt/fridgestare && ./ops/backup.sh >> /var/log/fridgestare-backup.log 2>&1
```

`BACKUP_KEEP_DAYS` (default 14) controls pruning. Copy the dumps off the VM
periodically — a backup that lives only on the machine it backs up is not a backup.

Restore with `./ops/restore.sh backups/fridgestare-<timestamp>.sql.gz`. It stops the
backend, loads the dump, and starts it again.

## 7. Updating

```bash
cd /opt/fridgestare
./ops/backup.sh
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f backend
```

Migrations run automatically on backend start. MariaDB DDL is not transactional, so a
migration that fails halfway leaves partially applied DDL with `alembic_version`
unchanged — that is exactly what the pre-update backup is for.

## 8. Operating notes

- **One worker on purpose.** The scheduler and the login rate limiter both keep state
  in process memory. Two workers would mean two schedulers racing to send the same
  email. Scaling out needs a shared store for both first; for one household, one
  worker is plenty.
- **Logs.** `docker compose -f docker-compose.prod.yml logs -f backend`. Set
  `LOG_LEVEL=DEBUG` in `.env` and restart the backend for more detail.
- **API docs** are off in production. Set `DOCS_ENABLED=true` and restart to expose
  `/docs` temporarily while debugging.
- **Certificates** renew automatically. They live in the `caddy-data` volume — don't
  delete it, or every restart re-issues and Let's Encrypt's rate limits will bite.
- **Fonts** come from Google Fonts, allowed explicitly in the Caddyfile's
  Content-Security-Policy. To cut that third-party request, self-host the two families
  and drop the font hosts from the policy.
