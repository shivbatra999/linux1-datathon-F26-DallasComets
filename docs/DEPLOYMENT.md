# LinuxONE deployment and local viewing

## Prerequisites

- LinuxONE s390x host, Docker Engine, Docker Compose, sufficient build disk/RAM, and network access to Supabase and dependency/model sources.
- An existing Supabase project with businesses, profiles, menu_items, orders, order_items, Auth accounts, signup/profile provisioning, grants, and row-level-security policies.
- Apply reviewed incremental files under `supabase/migrations/` in order. These files do not bootstrap all tables/policies. Export the missing schema/policies before claiming fresh-project reproducibility.
- Existing profile keys under the deployment user's `~/.config/simplecater/keys/`; see [key setup](PROFILE_ENCRYPTION.md). Do not regenerate keys for an existing database.
- The tested host and container user have UID 1000. Check ownership before deploying on another host.

## Configure without exposing secrets

From the repository root, if `.env` does not already exist:

```bash
cp .env.example .env
chmod 600 .env
nano .env
```

Required: `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY`. Use a publishable key, not a secret/service-role key. Configure actual test accounts outside source control.

Compose sets the app's origin from `SIMPLECATER_DEPLOY_ORIGIN` (default `http://127.0.0.1:8000`) and forces its Granite URL to `http://granite:8080/v1`. The source `.env.example` separately documents direct Python execution on port 8001 and loopback Granite access. For a Mac-to-LinuxONE model tunnel, use the local forwarded model port (for example 8081) in the direct-execution LLM URL.

Do not print plain `docker compose config` into shared output; it resolves environment secrets. Validate safely:

```bash
docker compose config --quiet
```

## Build and run

```bash
docker compose build app
docker compose up -d --no-deps --no-build app
docker compose up -d --build granite
```

A fresh Granite build needs its image build and first model download/conversion. Existing deployments can reuse the image with `docker compose up -d --no-deps --no-build granite`. Avoid `down -v`; the model volume is persistent. Private keys are an external bind mount, not inside an image or named app volume.

The Python build on s390x may compile SciPy, NumPy, scikit-learn, and cryptography from source. gfortran/OpenBLAS/LAPACK and runtime libraries are included in the Dockerfile. This can take tens of minutes; use a second terminal to follow logs rather than canceling the build.

```bash
docker compose --progress plain build app > /tmp/simplecater-build.log 2>&1
# In a separate SSH terminal:
tail -f /tmp/simplecater-build.log
```

## Verify

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
curl --max-time 10 http://127.0.0.1:8000/health
curl --max-time 10 http://127.0.0.1:8080/health
```

App: `127.0.0.1:8000`; Granite: `127.0.0.1:8080`. Granite can return 503 while loading, then 200 when ready. Health does not prove successful inference or authentication. Browser/API smoke tests must also pass.

Private connectivity check:

```bash
docker compose exec -T app python -c 'import httpx; r=httpx.get("http://granite:8080/health", timeout=15); print(r.status_code); r.raise_for_status()'
```

## View from a Mac

Run on the Mac, from the directory containing your SSH key:

```bash
ssh -i first.pem -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -L 8000:127.0.0.1:8000 linux1@YOUR_LINUXONE_HOST
```

Keep the tunnel open and visit `http://127.0.0.1:8000/index.html`. Use exactly this host/port to match Origin checks. If the local port is occupied, investigate first; changing it also requires an approved origin configuration. The website is viewed locally, but application/model execution stays on LinuxONE.

Public deployment requires HTTPS, the matching `SIMPLECATER_DEPLOY_ORIGIN`, and appropriate trusted ingress. The tested demo uses SSH, not a published HTTPS website.

## Source and automatic deployment

`.github/workflows/deploy.yaml` triggers on pushes to main and runs `git switch main`, `git pull --ff-only`, then `docker compose up -d --build`. Check GitHub Actions for success; a merge alone is not proof of deployment.

The host's local main previously diverged from origin/main. Preserve local commits/branches and reconcile the deployment checkout before relying on this workflow; do not force-reset a dirty or divergent checkout. A feature-branch manual deployment can be healthy even while automatic deployment fails.

Before edits inspect `git status --short`, current branch, and commit. A running container retains the code copied at build time even if the host switches branches. Do not treat the host branch name or `/health` as the container's deployed version.

## Secondary test deployment

`compose.encryption.yaml` is a standalone profile test deployment, not an override to merge into the default stack:

```bash
docker compose -p simplecater-encryption -f compose.encryption.yaml up -d --build
```

It uses loopback port 8002 and existing read-only keys but does not define the Granite service or a shared AI network. It is not the final assembled AI deployment. The obsolete app_data volume in the default stack is not the live database; live data is in Supabase.

## Final inventory

Record dependency versions and the image/llama.cpp/model revisions used for the submission. `docker compose exec -T app python -m pip freeze` prints packages rather than application secrets. Keep actual credentials, private keys, and decrypted profiles out of logs and Git.
