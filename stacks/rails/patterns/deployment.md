# Rails Deployment Patterns (Kamal 2 + Thruster)

`rails new` (Rails 8) generates everything needed to ship with Kamal 2: a
production `Dockerfile`, `config/deploy.yml`, `.kamal/secrets`, `bin/kamal`, and
Thruster in front of Puma. Read the generated files before changing them; they
are the source of truth, this file explains them.

---

## 1. The Pieces

| Piece | What it does |
|-------|--------------|
| **Kamal 2** (`bin/kamal`) | Builds the Docker image, pushes it to a registry, boots containers on your servers over SSH, swaps traffic with zero downtime |
| **kamal-proxy** | Reverse proxy Kamal runs on each server: TLS via Let's Encrypt, health-checked cut-over between old and new containers |
| **Thruster** (`bin/thrust`) | Small proxy inside the app container: HTTP/2, gzip, asset caching, X-Sendfile. Listens on port 80, forwards to Puma on 3000 |
| **Solid Queue / Cache / Cable** | Database-backed jobs, cache and pub/sub, so a single server needs no Redis |

The Dockerfile ends with:

```dockerfile
ENTRYPOINT ["/rails/bin/docker-entrypoint"]   # runs db:prepare before the server starts
EXPOSE 80
CMD ["./bin/thrust", "./bin/rails", "server"]
```

---

## 2. `config/deploy.yml`

```yaml
service: myapp
image: myorg/myapp

servers:
  web:
    - 192.0.2.10
  job:                              # optional: separate worker container
    hosts:
      - 192.0.2.10
    cmd: bin/jobs

proxy:
  ssl: true
  host: app.example.com
  healthcheck:
    path: /up                       # Rails 8 route: get "up" => "rails/health#show"

registry:
  server: ghcr.io
  username: myorg
  password:
    - KAMAL_REGISTRY_PASSWORD

env:
  secret:
    - RAILS_MASTER_KEY
  clear:
    SOLID_QUEUE_IN_PUMA: true       # drop this when the job role above runs bin/jobs
    WEB_CONCURRENCY: 2

volumes:
  - "myapp_storage:/rails/storage"  # SQLite databases and Active Storage disk files

asset_path: /rails/public/assets    # keeps old fingerprinted assets reachable during deploys

builder:
  arch: amd64

aliases:
  console: app exec --interactive --reuse "bin/rails console"
  logs: app logs -f
```

If the app's health route is `/health` (not `/up`), set `proxy.healthcheck.path`
to match, or the deploy hangs waiting for a healthy container.

---

## 3. Secrets

`.kamal/secrets` is committed and holds **references**, never values:

```bash
KAMAL_REGISTRY_PASSWORD=$KAMAL_REGISTRY_PASSWORD
RAILS_MASTER_KEY=$(cat config/master.key)
# Or from a password manager:
# SECRETS=$(kamal secrets fetch --adapter 1password --account myteam --from Vault/myapp KEY1 KEY2)
# DATABASE_PASSWORD=$(kamal secrets extract DATABASE_PASSWORD $SECRETS)
```

Application secrets belong in `bin/rails credentials:edit` (encrypted, unlocked by
`RAILS_MASTER_KEY`), not in `env.clear`.

---

## 4. Databases

**PostgreSQL / MySQL**: use a managed database, or run it as a Kamal accessory:

```yaml
accessories:
  db:
    image: postgres:17
    host: 192.0.2.10
    port: "127.0.0.1:5432:5432"
    env:
      secret:
        - POSTGRES_PASSWORD
    directories:
      - data:/var/lib/postgresql/data
```

**SQLite** (supported in production on Rails 8): all databases (primary, queue,
cache, cable) live in `storage/` on the mounted volume. That ties the app to one
server, and the volume is the only copy of the data: set up backups before going
live, e.g. Litestream streaming to S3 (as an accessory or a sidecar process), and
test a restore.

---

## 5. Commands

```bash
bin/kamal setup            # first deploy: installs Docker, boots proxy, accessories and app
bin/kamal deploy           # build, push, boot new containers, cut over
bin/kamal rollback <ver>   # boot a previous image version
bin/kamal app logs -f      # or the `logs` alias
bin/kamal console          # alias above: Rails console in the running container
bin/kamal app exec "bin/rails db:migrate:status"
```

---

## 6. Migrations and Zero-Downtime Deploys

`bin/docker-entrypoint` runs `bin/rails db:prepare` when the web container starts,
so migrations run during the deploy, **while the old version still serves
traffic**. Every migration must be compatible with the code currently running:

- Add columns nullable or with a default; backfill in a job; add `NOT NULL` later.
- Remove a column in two deploys: `self.ignored_columns += ["old"]` first, drop it next.
- Rename = add new + backfill + switch reads + drop old (never `rename_column` live).
- Large-table indexes on PostgreSQL: `algorithm: :concurrently` with `disable_ddl_transaction!`.

---

## 7. Checklist Before a First Deploy

- [ ] `config/deploy.yml` host, registry and image names set; DNS points at the server
- [ ] `proxy.healthcheck.path` matches a route that returns 200 without auth
- [ ] `config.assume_ssl` and `config.force_ssl` stay on in production (Rails 8 default behind kamal-proxy)
- [ ] Jobs: `SOLID_QUEUE_IN_PUMA` **or** a `job` role, not both
- [ ] Persistent data on a volume (`storage/`) or an external service; backups for SQLite
- [ ] `bin/kamal setup` run once; later deploys use `bin/kamal deploy`
