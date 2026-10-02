# Local SearXNG example

This directory contains a minimal local SearXNG configuration for Cluefinch MCP.

SearXNG is a separate project and service licensed under AGPL-3.0. This example does not include SearXNG source code; Docker Compose retrieves the upstream image.

## Requirements

- Docker with Docker Compose support

## 1. Create a local secret

Create a `.env` file in this directory containing a random `SEARXNG_SECRET`.

On macOS or Linux:

```sh
printf 'SEARXNG_SECRET=%s\n' "$(openssl rand -hex 32)" > .env
```

On Windows PowerShell:

```powershell
$secret = -join ((1..64) | ForEach-Object { '{0:x}' -f (Get-Random -Maximum 16) })
"SEARXNG_SECRET=$secret" | Set-Content -Encoding ascii .env
```

Do not commit the generated `.env` file.

## 2. Start SearXNG

```sh
docker compose up -d
```

The service is bound to loopback only and is available at:

```text
http://127.0.0.1:8081
```

Cluefinch uses this address by default.

## 3. Stop SearXNG

```sh
docker compose down
```

If you already operate SearXNG elsewhere, you do not need this example. Point Cluefinch to your existing instance with `MCP_SEARCH_SEARXNG_URL`.

For licensing and deployment considerations, see [SearXNG integration and release requirements](../../docs/SEARXNG_COMPLIANCE.md).
