# Cluefinch MCP security policy

No security response SLA or supported-version commitment has been established.

## Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/cluefinch/mcp-server/security/advisories/new)
on [cluefinch/mcp-server](https://github.com/cluefinch/mcp-server):
open **Security → Advisories → Report a vulnerability**. Do not put vulnerability
details in public Issues. Alternatively, send vulnerability reports privately to
security@cluefinch.com.

Include the affected version, operating system,
minimal reproduction, expected and observed behavior, and impact. Remove secrets
and personal data from logs and examples.

## Deployment scope

The sample deployment binds SearXNG to loopback and disables its limiter for local
use. It is not a public-service deployment profile. A hosted deployment needs
authentication, abuse controls, network isolation, and a separate data policy.
Retrieved pages are untrusted content; SSRF controls do not prevent prompt
injection in a consuming agent. See README.md for the implemented boundaries.
