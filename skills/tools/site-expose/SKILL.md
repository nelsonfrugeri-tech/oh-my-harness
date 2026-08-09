---
name: site-expose
description: Temporarily expose a local HTML report through a password-protected URL for access from another device. Use only after an explicit user request to publish, open on a phone, or share temporarily; require an authenticated tunnel, verify unauthorized and authorized responses, keep credentials out of files, and provide exact teardown.
---

# Site Expose

Public exposure is an outward-facing operation. Never run it while merely generating a report.

## Preconditions

1. Resolve the final HTML path and hash, then scan the exact file for credentials, tokens, private
   keys, PII, internal hostnames, and other content that should not leave the machine. Treat every
   match as a blocker until the user removes it or explicitly accepts the disclosed risk.
2. Explain that tunnel providers can observe traffic metadata and may process content. Show the
   exact path, hash, scan result, and provider, then obtain fresh explicit confirmation to expose
   that artifact. A prior request made before generation is not sufficient.
3. Resolve the abstract `tunnel` capability from the active harness instructions.
4. If no provider is configured, report the local file and the missing capability; do not install or
   expose anything without the user's authorization.
5. Generate a high-entropy password for this run. Keep it only in process environment and the chat;
   never write it to the repository, report directory, logs, shell history, or a reusable config.
   Disclose that the chat transcript retains the credential until the session data is removed; keep
   the exposure short-lived and stop it promptly.
6. Warn that the URL is temporary and must not be forwarded.

Use [scripts/auth_server.py](scripts/auth_server.py) as the loopback-only authenticated origin when
the selected tunnel provider does not supply authentication itself.

## Start safely

Create the runtime directory with `mktemp -d` and mode `0700` for PID files and non-secret logs.
Start the origin and tunnel as separate processes and record each exact PID. Never use `pkill -f`,
process-name matching, or a broad kill command; those can terminate unrelated user services.

The authenticated origin requires:

```text
SITE_ROOT=/absolute/site/path
SITE_SHA256=<approved-lowercase-sha256>
AUTH_USER=<generated-or-current-user>
AUTH_PW=<fresh-random-password>
PORT=<dynamically allocated loopback port>
```

Select a provider through `tunnel`; provider-specific command syntax belongs to the configured
provider. The origin must verify `SITE_SHA256` at startup and serve the resulting immutable byte
snapshot for the lifetime of the process. Bind the origin to loopback and point the tunnel only at
that origin.

## Verification gate

Do not reveal the public URL until all checks pass:

| Endpoint | Without credentials | With credentials |
| --- | ---: | ---: |
| Loopback origin | `401` | `200` |
| Public tunnel | `401` | `200` |

Reject a public URL unless it uses `https://` with valid TLS. Basic Auth over HTTP exposes the
credential in cleartext; never reveal the one-time credentials or proceed with an HTTP endpoint.

Also verify that the response is the expected report, not a default page. A public `200` without
credentials is an incident: stop the exact tunnel PID immediately, fix authentication, and repeat
the full gate.

## Delivery

Show the URL, username, and one-time password together. State that the URL disappears when the host
sleeps or the processes stop, and ask the user to request teardown when finished.

## Teardown

Read the recorded PID files, confirm each PID still belongs to the process started by this run, send
`TERM`, wait for exit, and use `KILL` only for the same verified PID if it does not stop. Remove the
runtime directory afterward and confirm the public endpoint is unreachable. Never affect another
site, tunnel, or local server.
